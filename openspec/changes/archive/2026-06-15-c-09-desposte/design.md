## Context

BASILE es un SaaS multiempresa para carnicerías. El flujo de compra → desposte → stock es el corazón operativo. C-08 (compras-media-res) ya registra compras de media res con peso total y costo total. C-09 debe permitir despostar esa compra en 12 cortes estándar, calcular rendimiento y merma, asignar costos proporcionales, y generar stock automáticamente.

Stack actual: FastAPI (async), SQLModel, PostgreSQL, React SPA, Zustand. Patrones establecidos en C-05 (productos) y C-08 (compras): Pydantic schemas con `extra='forbid'`, inyección de dependencias (`db: AsyncSession`, `current_user`, `tenant`), `Decimal` para dinero, índices en `empresa_id`, transacciones ACID.

## Goals / Non-Goals

**Goals:**
- Registrar un desposte vinculado a una compra de media res existente.
- Permitir agregar hasta 12 cortes por desposte con kilos obtenidos.
- Calcular automáticamente rendimiento total, merma, porcentaje por corte, costo asignado y costo final por kilo.
- Validar que rendimiento total ≤ peso total de la compra.
- Generar `MovimientoStock` tipo `entrada_desposte` por cada corte al finalizar.
- Registrar auditoría con snapshot completo al finalizar.
- Frontend: wizard paso a paso con cálculos en vivo.

**Non-Goals:**
- No se permite editar un desposte finalizado (solo lectura).
- No se permite despostar una compra parcialmente (una compra → un desposte en v1.0; multi-desposte en v2.0 a definir).
- No se incluyen cortes personalizados más allá de los 12 fijos ("otros" cubre el resto).
- No se recalculan costos históricos de productos al finalizar (solo se genera el movimiento de stock; el costo del producto se actualiza en C-19 rentabilidad).

## Decisions

1. **Modelo de datos: tabla separada `corte_desposte` con FK a `desposte`**
   - *Rationale*: Un desposte tiene N cortes. Normalizar en tabla separada permite queries de rendimiento por corte y mantener historial completo.
   - *Alternativa considerada*: JSONB en `desposte.cortes` — rechazada por dificultad de indexar, validar y relacionar con productos.

2. **Enum de tipo_corte en código (Pydantic/SQLModel), no en DB enum**
   - *Rationale*: Los 12 cortes son fijos por regla de negocio (RN-DESP-02). Usar `Literal` en Pydantic y `String` en DB da flexibilidad para migraciones sin bloqueos. Seed data no necesaria porque los valores son constantes en código.
   - *Alternativa considerada*: Tabla `tipo_corte` — rechazada por overhead innecesario para 12 valores fijos.

3. **Cálculo de costo asignado = (costo_total_compra / peso_total_compra) * kilos_obtenidos del corte**
   - *Rationale*: Distribución proporcional simple y predecible. Cada corte lleva el costo de la compra ponderado por su peso.
   - *Alternativa considerada*: Distribución manual por el usuario — se deja para futuro si el negocio lo requiere; en v1.0 es automática para reducir errores.

4. **Generación de stock en transacción ACID dentro del servicio `finalizar_desposte`**
   - *Rationale*: El desposte y sus movimientos de stock deben ser atómicos. Si falla algún movimiento, se hace rollback completo.
   - *Alternativa considerada*: Eventos asíncronos (cola) — rechazada por complejidad innecesaria; el desposte es síncrono por naturaleza.

5. **Estado del desposte: `en_proceso` y `finalizado`**
   - *Rationale*: Permite agregar cortes incrementalmente y validar antes de congelar. Solo `finalizado` genera stock y auditoría.
   - *Alternativa considerada*: Sin estado, todo en un solo POST — rechazada por UX del frontend (wizard paso a paso) y necesidad de validación previa.

6. **RLS en tablas `desposte` y `corte_desposte`**
   - *Rationale*: Capa de seguridad adicional al aislamiento por `empresa_id` en queries. Multi-tenant por diseño.

## Risks / Trade-offs

- **[Risk] Rendimiento total excede peso de compra por errores de tipeo** → Mitigación: Validación estricta en backend (`rendimiento_total <= peso_total_compra`) y advertencia visual en frontend cuando se acerca al límite.
- **[Risk] Producto destino no existe para un corte** → Mitigación: El frontend solo muestra productos existentes de la empresa. Si un corte no tiene producto mapeado, se registra sin `producto_id` y no genera stock (con advertencia al usuario). El mapeo corte→producto se resuelve en configuración manual o seed data inicial.
- **[Risk] Precisión decimal en cálculos de costo** → Mitigación: Usar `Decimal` en todo el backend con contexto de precisión definido. Redondeo a 2 decimales para costos, 3 decimales para kilos.
- **[Trade-off] Un desposte por compra en v1.0** → Si una compra grande se desposta en dos días, se requiere registrar como dos compras separadas. Esto simplifica el modelo pero puede generar duplicación de datos de compra. Se acepta para v1.0.

## Migration Plan

1. Crear migraciones Alembic: `desposte` y `corte_desposte`.
2. Agregar índices: `(empresa_id)`, `(compra_id)`, `(desposte_id)`, `(producto_id)`.
3. Activar RLS en nuevas tablas.
4. Seed data: no requiere (cortes son enum en código).
5. Rollback: eliminar tablas con `alembic downgrade`.

## Open Questions

1. ¿Se requiere mapeo automático corte→producto por nombre (ej: "asado" → producto con nombre "asado") o es manual? → **Decisión v1.0**: manual por el usuario en el wizard; el sistema sugiere productos que coincidan por nombre pero no impone.
2. ¿Se permite anular un desposte finalizado? → **Decisión v1.0**: no. Requiere Admin/Encargado y se maneja como ajuste de stock manual en C-10.
3. ¿Se requiere soporte para desposte de "cuarto de res" además de media res? → **Decisión v1.0**: no. El modelo soporta cualquier peso, pero la UX está diseñada para media res.
