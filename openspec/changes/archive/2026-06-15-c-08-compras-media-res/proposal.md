## Why

La carnicería necesita registrar sistemáticamente las compras de media res a proveedores para controlar costos, calcular costo por kilo y habilitar el flujo de desposte. Sin este módulo, no hay trazabilidad de costos ni entrada de stock de productos primarios. Es un bloqueante para la épica de Desposte (US-010) y para el cálculo de rentabilidad (US-019).

## What Changes

- **Nueva tabla `compra`** con campos: fecha, proveedor_id, cantidad_medias_reses, peso_total, costo_total, costo_por_kilo (calculado), costo_promedio_historico, observaciones.
- **CRUD completo de compras** en backend (FastAPI) con validaciones estrictas: peso > 0, costo > 0, división por cero protegida.
- **Cálculo automático de `costo_por_kilo`** al crear o actualizar compra: `costo_total / peso_total` con precisión decimal.
- **Entrada automática de stock** al crear compra: genera `MovimientoStock` tipo `entrada_compra` para producto genérico "Media Res" (o queda disponible para desposte según configuración).
- **Historial de compras por proveedor**: el endpoint `GET /proveedores/{id}/historial` (existente desde C-07) se popula con datos reales de compras.
- **Soft delete** en compras: no se eliminan físicamente; se marcan como inactivas o anuladas para preservar historial financiero.
- **Frontend**: grid de compras, formulario de alta/edición, vista de detalle con costo por kilo destacado.
- **Tests**: TDD obligatorio — tests de backend primero, luego implementación.

## Capabilities

### New Capabilities
- `compras-crud`: CRUD completo de compras de media res con validaciones y cálculos automáticos.
- `compras-stock-integration`: Entrada automática de stock (`MovimientoStock`) vinculada a compra.
- `proveedores-historial`: Endpoint de historial de compras por proveedor con datos reales (población del endpoint existente en C-07).

### Modified Capabilities
- `proveedores-crud` (C-07): Se extiende el router de proveedores para incluir `GET /proveedores/{id}/historial` con datos de compras. No cambia el contrato de la spec existente, solo se popula con datos reales.

## Impact

- **Backend**: Nuevo router `/compras`, nuevo servicio `CompraService`, nuevo SQLModel `Compra`, schemas Pydantic, migration Alembic.
- **Frontend**: Nuevas pantallas en el módulo de Compras (grid, form, detail), Zustand store para estado de compras.
- **Base de datos**: Nueva tabla `compra` con FK a `proveedor` e `empresa`; índices en `empresa_id`, `fecha`, `proveedor_id`.
- **Dependencias**: Requiere C-05 (productos-catalogo) para producto genérico de media res y C-07 (proveedores) para FK y endpoint de historial.
- **Seguridad**: Todas las queries filtradas por `empresa_id`; RLS en tabla `compra`.
