## Context

El change C-03 (`empresa-config`) dejó operativa la entidad `Empresa` con soft-delete, logo upload y aislamiento multi-tenant. C-02 (`auth-core`) y C-04 (`usuarios-rbac`) dejan operativo el middleware de autenticación JWT con claims `user_id`, `empresa_id`, `rol`, y el middleware RBAC que protege recursos por rol. El modelo `CategoriaProducto` ya existe en `backend/src/modules/producto/models.py` pero está vacío de lógica de negocio y carece de índices. El modelo `Producto` no existe todavía.

Este change es **prerequisito estricto** de C-08 (compras), C-10 (stock), C-11 (balanza SYSTEL) y C-12 (ventas). Sin productos con PLU y precios, ningún flujo operativo puede avanzar.

## Goals / Non-Goals

**Goals:**
- Habilitar el catálogo completo de productos con CRUD, búsqueda, cálculo de margen y baja lógica.
- Habilitar CRUD de categorías de producto con seed inicial por empresa.
- Implementar importación masiva desde Excel QUENDRA con preview, validación y detección de duplicados.
- Entregar la capa frontend de productos: grid, formulario, modal de importación.
- Mantener TDD: tests escritos antes del código productivo para toda lógica de negocio.

**Non-Goals:**
- No se implementa kardex de stock en este change (C-10).
- No se implementa lectura de balanza SYSTEL (C-11).
- No se implementa auditoría de operaciones sobre productos (C-20).
- No se implementa notificaciones de stock bajo (C-20).
- No se soporta importación desde formatos distintos a QUENDRA xlsx.

## Decisions

### 1. Almacenar margen calculado en columna `margen` en lugar de calcularlo on-the-fly
**Rationale**: El margen se consulta frecuentemente en listados, grids y reportes (C-19 rentabilidad). Calcularlo en cada lectura es innecesario y costoso para agregaciones. Almacenarlo garantiza lecturas O(1) y evita inconsistencias si el cálculo cambia en el futuro.
**Alternativa considerada**: `@property` o `hybrid_property` en SQLAlchemy — descartada porque no permite indexación ni lectura eficiente en queries agregadas.

### 2. Índice compuesto `(empresa_id, plu)` con `unique=True`
**Rationale**: RN-PROD-01 exige PLU único por empresa. Un índice compuesto único garantiza la constraint a nivel de base de datos (evita race conditions en concurrencia) y acelera la búsqueda por PLU que es el path crítico de la balanza SYSTEL (C-11).
**Alternativa considerada**: Validación por aplicación (query previa) — descartada porque no es atómica y falla bajo concurrencia.

### 3. Seed de categorías se crea como copia por empresa, no como referencia global
**Rationale**: Las categorías seed (Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros) deben poder renombrarse o eliminarse por empresa sin afectar a otras. Una tabla global con FK obligaría a restricciones innecesarias. Copiarlas al crear la empresa da autonomía total.
**Alternativa considerada**: Tabla `categoria_global` + `empresa_categoria` — descartada por complejidad innecesaria en v1.0.

### 4. Importación QUENDRA: preview en memoria (Redis/cache) con confirmación separada
**Rationale**: El usuario necesita ver qué se va a importar antes de comprometer la base de datos. Generar un `preview_session_id` con TTL (ej. 10 minutos) permite validar filas, mostrar errores y luego confirmar en un segundo request. Esto evita transacciones largas abiertas durante la revisión del usuario.
**Alternativa considerada**: Transacción única con rollback si hay errores — descartada porque no permite preview interactivo.

### 5. Decimal(19,4) para todos los campos monetarios y de peso
**Rationale**: RN-GLOBAL y reglas duras del proyecto prohíben `float` para dinero. `Decimal(19,4)` da 15 dígitos enteros + 4 decimales, suficiente para precios argentinos (ARS con alta inflación) y stock en kilos con precisión de 3 decimales (RN-STOCK-01 pide 3 decimales; usamos 4 para sobrar).
**Alternativa considerada**: `NUMERIC(12,2)` — descartada por riesgo de overflow con precios altos y falta de precisión para stock.

### 6. Soft-delete (`activo = false`) en lugar de eliminación física
**Rationale**: RN-GLOBAL-02 prohíbe eliminación física de registros con historial. Un producto inactivo desaparece de búsquedas por defecto pero preserva referencias en ventas pasadas, despostes y movimientos de stock.
**Alternativa considerada**: Eliminación física con cascada — descartada por violar reglas de negocio.

### 7. Búsqueda por PLU o nombre con `ilike` + índice funcional
**Rationale**: La búsqueda rápida por PLU o nombre es un requisito funcional (US-005 CA-2). Un índice funcional `lower(nombre)` acelera búsquedas case-insensitive. La búsqueda por PLU usa el índice compuesto único. Para búsquedas parciales de nombre usamos `ilike '%term%'` con paginación; si el volumen lo justifica, se evaluará `pg_trgm` en futuras iteraciones.
**Alternativa considerada**: Full-text search (TSVector) — descartada para v1.0 por sobredimensionamiento; `ilike` es suficiente para catálogos de <10k productos por empresa.

## Risks / Trade-offs

- **[Risk]** El parser de Excel QUENDRA puede fallar con formatos no estándar o versiones antiguas de Excel.
  → **Mitigation**: Documentar formato esperado; soportar `.xlsx` exclusivamente (no `.xls`); usar `openpyxl` que soporta Office 2007+; capturar excepciones de parsing y devolver error claro al usuario.

- **[Risk]** Importación masiva de 5000 filas puede generar carga significativa en el event loop async de FastAPI.
  → **Mitigation**: Usar `asyncio.to_thread` o `BackgroundTasks` para el parsing del archivo; limitar a 5000 filas; procesar en chunks de 100 filas dentro de la transacción de confirmación.

- **[Risk]** El cálculo de margen almacenado puede quedar desfasado si se actualiza el costo por vía externa (ej. desposte en C-09).
  → **Mitigation**: El costo por kilo del producto se actualiza explícitamente por el desposte (C-09) o por edición manual. En ambos casos el trigger/aplicación recalcula el margen. No hay vía de actualización silenciosa.

- **[Risk]** Preview en memoria (Redis/cache) puede perderse si el TTL expira antes de que el usuario confirme.
  → **Mitigation**: TTL de 10 minutos con mensaje claro al usuario; permitir re-subir el archivo si expiró; no generar estado crítico en el preview.

- **[Trade-off]** No implementamos `pg_trgm` para búsquedas de texto: sacrifica performance en búsquedas muy grandes a cambio de simplicidad operativa. Para catálogos típicos de carnicería (<5k productos) `ilike` es suficiente.

## Migration Plan

1. Crear migración Alembic que agregue tablas `producto` y `categoria_producto` con índices y constraints.
2. Activar RLS en ambas tablas con policy `empresa_id = current_setting('app.current_empresa')::uuid`.
3. Seed data: para empresas existentes, correr script que cree las 5 categorías seed si no las tienen.
4. Deploy backend con nuevos routers; deploy frontend con nuevos feature modules.
5. Rollback: revertir migración Alembic; los productos no afectan datos históricos porque es el primer change que los crea.

## Open Questions

1. ¿El formato exacto de exportación QUENDRA tiene columnas fijas o admite variación? (Se asume formato fijo basado en mapeo estándar; validar con usuario real si es posible.)
2. ¿Se requiere importación incremental (actualizar productos existentes por PLU) o solo creación? (Se asume creación solo; actualización masiva se evalúa en v2.)
3. ¿Se requiere historial de cambios de precios? (No en v1.0; C-20 auditoría registra snapshots de acciones, no series temporales de precios.)
