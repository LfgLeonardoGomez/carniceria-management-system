## Why

BASILE es un SaaS para gestión de carnicerías. El módulo de ventas y cobro es el núcleo operativo donde se conecta el catálogo de productos, el stock, la caja y las cuentas corrientes. Sin este módulo, el sistema no puede realizar la operación diaria de una carnicería. Actualmente existen stubs vacíos en `backend/src/modules/venta/` y no hay pantalla de caja en el frontend. Es el siguiente paso crítico en el camino hacia un MVP operativo.

## What Changes

- **Backend (FastAPI)**:
  - Modelos SQLModel: `Venta`, `DetalleVenta`, `PagoVenta` con relaciones y constraints.
  - Servicio de ventas: creación, cálculos de subtotal/total, precios por tipo de cliente, transiciones de estado (máquina de estados).
  - Router `/ventas`: endpoints para crear, suspender, cobrar, anular y recuperar ventas.
  - Integración con `MovimientoStock` (salida_venta) al cobrar, con rollback en anulación.
  - Integración placeholder con `MovimientoCaja` (C-13 no implementado aún) y `CuentaCorriente` (C-14 no implementado aún).
  - Validaciones estrictas: stock no negativo, caja abierta, permisos RBAC por estado.
  - Tests unitarios e integración con testcontainers (PostgreSQL real).

- **Frontend (React + Vite + Zustand)**:
  - Pantalla POS/Caja completa: lector SYSTEL (integra C-11), selección de cliente, carrito, subtotal, descuentos, total, medios de pago.
  - Acciones: Cobrar, Suspender, Recuperar venta suspendida, Anular (solo Admin/Encargado).
  - Vista de ticket/imprimible post-cobro.

- **Migración Alembic**: tablas `venta`, `detalle_venta`, `pago_venta`.

## Capabilities

### New Capabilities
- `venta-core`: Creación de venta con carrito, cálculo de subtotal/total, precios automáticos según tipo de cliente, snapshot de tipo_cliente_al_momento.
- `venta-estados`: Máquina de estados (`en_curso` → `suspendida`/`cobrada`/`anulada`), transiciones controladas, suspensión y recuperación, anulación con reversión.
- `venta-pagos`: Medios de pago (efectivo, transferencia, débito, crédito, cuenta_corriente), integración con stock, caja (placeholder) y cuenta_corriente (placeholder).
- `venta-ticket`: Generación de comprobante/ticket post-cobro (placeholder para v1.0: JSON imprimible).
- `pos-frontend`: Pantalla de caja completa con carrito, cliente, descuentos, medios de pago y acciones de cobro/suspensión/anulación.

### Modified Capabilities
- (Ninguno. Este change introduce un módulo nuevo desde cero.)

## Impact

- **Nuevos archivos**:
  - `backend/src/modules/venta/models.py`
  - `backend/src/modules/venta/schemas.py`
  - `backend/src/modules/venta/service.py`
  - `backend/src/modules/venta/router.py`
  - `backend/src/modules/venta/state_machine.py`
  - `backend/tests/modules/venta/...`
  - `frontend/src/pages/PosPage.tsx` y componentes asociados
  - Migración Alembic para tablas de venta
- **Módulos afectados**:
  - `stock-movimientos` (C-10): se consume para generar salidas de stock y validar stock disponible.
  - `clientes` (C-06): se consulta para obtener tipo de cliente y precios.
  - `productos-catalogo` (C-05): se consulta para obtener datos de productos por PLU.
  - `caja-operaciones` (C-13): se integra vía placeholder; C-12 creará `MovimientoCaja` mínimamente o asumirá stub.
  - `cuentas-corrientes` (C-14): se integra vía placeholder para generación de deuda automática.
- **Breaking**: Ninguno (módulo nuevo).
