## Context

BASILE es un SaaS multiempresa para carnicerías. El dominio de stock es el corazón operativo: sin stock no hay ventas. C-08 (compras) y C-09 (desposte) generan entradas automáticas de stock, pero el sistema carece de consulta, ajuste manual y alertas. Este change implementa el módulo completo de movimientos de stock (Kardex) con cálculo en tiempo real, validación de negativo y frontend operativo.

Stack actual:
- Backend: FastAPI + SQLModel + PostgreSQL (async)
- Frontend: React 18 + TypeScript strict + Zustand
- Auth: JWT con `empresa_id` en subclaim
- Testing: pytest-asyncio + testcontainers (PostgreSQL real)

## Goals / Non-Goals

**Goals:**
1. Registrar todo movimiento de stock (entrada_compra, entrada_desposte, salida_venta, ajuste) en tabla inmutable `MovimientoStock`.
2. Calcular stock actual por producto a partir de la sumatoria de movimientos (entradas positivas, salidas negativas).
3. Proveer kardex paginado por producto con `stock_resultante` snapshot.
4. Permitir ajustes manuales con motivo, restringidos a roles Encargado/Admin.
5. Bloquear cualquier operación que dejaría stock negativo (RN-STOCK-04).
6. Alertar productos con `stock_actual <= stock_minimo`.
7. Frontend: pantalla de stock, kardex, modal de ajuste, panel de alertas.

**Non-Goals:**
- Costo promedio ponderado o valorización de stock (método a definir en v1.1, ver RN-STOCK-07).
- Integración con hardware de balanza (C-11).
- Notificaciones push/email de alertas (C-20).
- Anulación de ventas con reversión de stock (se maneja en C-12).

## Decisions

### 1. Modelo de datos: tabla `MovimientoStock` como fuente de verdad
**Decisión**: El stock actual se calcula como `SUM(cantidad_kilos)` de todos los movimientos del producto. No se almacena stock actual denormalizado en `Producto` como fuente de verdad; `Producto.stock_actual` puede existir como cache pero se recalcula desde el kardex.
**Rationale**: Inmutabilidad y trazabilidad total. El snapshot `stock_resultante` en cada fila permite reconstruir el estado en cualquier momento sin recalcular todo el historial.
**Alternativa considerada**: Actualizar `Producto.stock_actual` en cada transacción. Rechazada porque rompe trazabilidad si hay race conditions o bugs.

### 2. Campos polimórficos `referencia_tipo` + `referencia_id`
**Decisión**: Usar string discriminator + string FK en lugar de tablas de unión o columnas nullable por tipo.
**Rationale**: Simplicidad. Las referencias pueden apuntar a `compra`, `desposte`, `venta` o `ajuste`. SQLModel no tiene herencia nativa de tabla única; este patrón es suficiente y performante con índice en `(referencia_tipo, referencia_id)`.

### 3. Índice compuesto `(empresa_id, producto_id, fecha)`
**Decisión**: Índice compuesto en esa columna y orden.
**Rationale**: Las consultas de kardex siempre filtran por empresa y producto, ordenadas por fecha. El índice cubre exactamente ese patrón de acceso.

### 4. Cálculo de stock en servicio, no en trigger de DB
**Decisión**: El cálculo de `stock_resultante` y la validación de negativo ocurren en el servicio de Python, no en triggers PostgreSQL.
**Rationale**: Control total de lógica de negocio en código, testeable, portable. Los triggers ocultan lógica y dificultan debugging.
**Trade-off**: Requiere `SELECT FOR UPDATE` o atomicidad por producto para evitar race conditions en entornas concurrentes. En v1.0 asumimos operación secuencial por empresa; si hay concurrencia real, se agregará advisory lock por `(empresa_id, producto_id)`.

### 5. Ajustes manuales como movimientos tipo `ajuste`
**Decisión**: Los ajustes manuales crean filas `MovimientoStock` con `tipo = ajuste`. La cantidad puede ser positiva (ajuste +) o negativa (ajuste -).
**Rationale**: Unifica el modelo. Todo cambio de stock pasa por la misma tabla. El motivo se guarda en un campo `motivo` (string) dentro del registro o en JSON asociado.

### 6. Roles para ajustes: Encargado o Admin
**Decisión**: Solo usuarios con rol `Encargado` o `Administrador` pueden ejecutar `POST /stock/ajustes`.
**Rationale**: Los ajustes manuales son operaciones de alto riesgo (pueden ocultar pérdidas o errores). El cajero/vendedor no debe tener este permiso.

## Risks / Trade-offs

- **[Riesgo] Performance del cálculo de stock con muchos movimientos**: Si un producto tiene miles de movimientos, `SUM(cantidad_kilos)` puede volverse lento.  
  → **Mitigación**: El índice compuesto acelera el filtro. A futuro se puede agregar un snapshot periódico (tabla `StockSnapshot`) para evitar recalcular desde el inicio de los tiempos.

- **[Riesgo] Race condition en validación de stock negativo**: Dos ventas concurrentes del mismo producto podrían pasar la validación individualmente y dejar stock negativo.  
  → **Mitigación**: En v1.0 se asume operación secuencial. Si aparece el problema, implementar advisory lock de PostgreSQL por `(empresa_id, producto_id)` o usar `SELECT FOR UPDATE` sobre una tabla de control de concurrencia.

- **[Trade-off] No se actualiza `Producto.stock_actual` automáticamente**: El frontend necesita stock actual rápido.  
  → **Mitigación**: El endpoint `GET /stock` calcula en tiempo real con `SUM`. Con índice adecuado esto es < 10ms para < 10k movimientos. Si es lento, se agrega un campo denormalizado actualizado en transacción.

## Migration Plan

1. Crear/verificar tabla `MovimientoStock` con todas las columnas requeridas.
2. Crear índice compuesto `(empresa_id, producto_id, fecha)`.
3. Implementar servicios y routers backend.
4. Implementar frontend.
5. Escribir tests TDD primero, luego código productivo.
6. Verificar que C-08 y C-09 generen movimientos con los campos polimórficos correctos.

## Open Questions

- ¿La tabla `MovimientoStock` ya existe incompleta por C-08/C-09? Si falta `stock_resultante` o `referencia_tipo`, se agrega vía migración.
- ¿Se requiere campo `motivo` en `MovimientoStock` o tabla separada `AjusteStock`? Decisión: campo `motivo` nullable en `MovimientoStock` para unificar.
