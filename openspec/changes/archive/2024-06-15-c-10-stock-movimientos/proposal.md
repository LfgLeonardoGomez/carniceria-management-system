## Why

El sistema BASILE necesita un módulo de stock para rastrear kilos de producto en tiempo real. Sin stock no hay ventas: C-08 (compras) y C-09 (desposte) generan entradas automáticas, pero el negocio requiere consultar stock actual, historial (kardex), ajustes manuales y alertas de faltantes. Este change habilita la visibilidad operativa del inventario y bloquea ventas que generen stock negativo (RN-STOCK-04).

## What Changes

- **Nueva tabla `MovimientoStock`** (Kardex): registro inmutable de entradas (compra, desposte), salidas (venta) y ajustes manuales. Incluye `stock_resultante` como snapshot y campos polimórficos `referencia_tipo` + `referencia_id`.
- **Índice compuesto** `(empresa_id, producto_id, fecha)` para consultas de kardex performantes.
- **Endpoints REST**:
  - `GET /stock` — stock actual por producto (calculado desde MovimientoStock).
  - `GET /stock/movimientos/{producto_id}` — kardex completo con paginación.
  - `POST /stock/ajustes` — ajustes manuales con motivo (solo Encargado/Admin).
  - `GET /stock/alertas` — productos con stock_actual <= stock_minimo.
- **Validación de stock negativo** (RN-STOCK-04): toda salida (venta o ajuste negativo) se bloquea si dejaría stock < 0.
- **Frontend**: pantalla de stock con grid, kardex por producto, modal de ajuste y panel de alertas.
- **Tests**: TDD obligatorio — cálculo de stock resultante, bloqueo negativo, alertas, paginación de kardex y aislamiento multi-tenant.

## Capabilities

### New Capabilities
- `stock-movimientos`: Consulta y gestión de inventario por kilos. Incluye cálculo de stock actual, kardex paginado, ajustes manuales con permisos y alertas de stock mínimo.

### Modified Capabilities
- *(ninguna — este change no modifica specs existentes, solo implementa nuevo dominio)*

## Impact

- **Backend**: nuevo router `/stock`, servicios de cálculo de stock, validación de negativo, queries con `empresa_id` obligatorio.
- **Frontend**: nuevas rutas, stores Zustand, componentes de grid, tabla de kardex, modal de ajuste, panel de alertas.
- **Base de datos**: tabla `MovimientoStock` con índice compuesto; posiblemente migración si faltan columnas en tabla existente de C-08/C-09.
- **Dependencias**: C-05 (productos-catalogo) debe existir para tener `Producto` con `stock_actual` y `stock_minimo`.
