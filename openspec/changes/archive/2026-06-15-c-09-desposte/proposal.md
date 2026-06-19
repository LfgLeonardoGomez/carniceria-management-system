## Why

El desposte es el corazón operativo de una carnicería: transforma la compra de media res en productos vendibles con costos asignados. Sin este módulo, BASILE no puede generar stock de cortes (asado, vacío, nalga, etc.) ni calcular rentabilidad real. Este change habilita el flujo completo compra → desposte → stock, prerrequisito estricto de ventas y reportes de rentabilidad.

## What Changes

- **Nuevo módulo de desposte** en backend y frontend para registrar el proceso de despiece de media res.
- **Endpoints REST** para crear desposte, agregar cortes, finalizar desposte, listar y obtener detalle.
- **Tablas `desposte` y `corte_desposte`** con FK a compra, operador y producto.
- **12 tipos de corte fijos**: asado, vacio, nalga, cuadril, peceto, bola_de_lomo, lomo, matambre, costilla, osobuco, molida, otros.
- **Cálculos automáticos**: rendimiento total, merma, porcentaje de rendimiento por corte, costo asignado proporcional, costo final por kilo.
- **Validación de negocio**: rendimiento total no puede superar el peso total de la compra origen.
- **Generación automática de stock**: al finalizar, se crean `MovimientoStock` tipo `entrada_desposte` por cada corte, vinculando `producto_id`.
- **Registro de auditoría**: acción `FINALIZAR_DESPOSTE` con snapshot completo del desposte y cortes.
- **Frontend**: wizard de desposte con selección de compra, tabla de cortes con cálculos en vivo, resumen de rendimiento/merma/costos.

## Capabilities

### New Capabilities
- `desposte-crud`: Creación, lectura y finalización de despostes vinculados a una compra de media res.
- `corte-desposte`: Administración de los 12 cortes dentro de un desposte, con cálculos de rendimiento y costos.
- `stock-automatico-desposte`: Generación automática de entradas de stock al finalizar un desposte.
- `auditoria-desposte`: Registro de auditoría al finalizar desposte con snapshot completo.

### Modified Capabilities
- `compras-media-res`: Agregar relación 1:N con desposte (campo ya existente en modelo, se activa su uso).
- `stock-movimientos`: Agregar tipo de movimiento `entrada_desposte` (extiende el enum de tipos).

## Impact

- **Backend**: Nuevo router `/despostes`, servicios de desposte, migraciones Alembic, schemas Pydantic, lógica de cálculos con `Decimal`.
- **Frontend**: Nuevas pantallas/rutas para wizard de desposte, tabla de cortes editable, componentes de resumen.
- **Base de datos**: Tablas `desposte` y `corte_desposte`; índices en `empresa_id`, `compra_id`, `desposte_id`.
- **Dependencias**: Requiere `C-08` (compras-media-res) completo para tener compras disponibles; `C-05` (productos) para vincular cortes a productos existentes.
- **Multi-tenancia**: Todas las queries filtran por `empresa_id`; RLS activo en nuevas tablas.
