## Context

BASILE es un SaaS multi-tenant para carnicerías. Los módulos de productos (C-05), clientes (C-06), stock (C-10), desposte (C-09) y usuarios/RBAC (C-04) están completos. El módulo de ventas (`backend/src/modules/venta/`) tiene un router stub de 3 líneas y modelos con un TODO. No existe service, schemas ni frontend para cobro.

Este change implementa el núcleo operativo: la creación, cobro, suspensión y anulación de ventas, con integración a stock, caja y cuenta corriente.

## Goals / Non-Goals

**Goals:**
- Modelar `Venta`, `DetalleVenta` y `PagoVenta` en SQLModel con constraints de precisión decimal.
- Implementar máquina de estados de venta con transiciones controladas y validaciones.
- Calcular subtotal/total con precios automáticos según tipo de cliente (snapshot al momento de la venta).
- Generar salidas de stock (`MovimientoStock` tipo `salida_venta`) de forma atómica al cobrar.
- Integrar placeholder con `MovimientoCaja` (C-13) y `CuentaCorriente` (C-14) para no bloquear el flujo.
- Proveer pantalla POS en React con carrito, cliente, descuentos, medios de pago y acciones.
- Tests de integración con PostgreSQL real (testcontainers) cubriendo cobro, suspensión, anulación, stock negativo bloqueado y CC automática.

**Non-Goals:**
- No se implementa C-13 (caja-operaciones) ni C-14 (cuentas-corrientes) completos; solo placeholders mínimos para que C-12 no se bloquee.
- No se implementa impresión física de ticket; se genera JSON imprimible (placeholder v1.0).
- No se implementa split payment (múltiples medios de pago) — v1.0 asume un único medio por venta (RN-PAGO-03).
- No se implementa alerta de límite de cuenta corriente excedido (RN-CLI-04 pendiente).
- No se implementa lectura SYSTEL en este change (pertenece a C-11); el frontend POS acepta input manual y PLU escaneado.

## Decisions

### 1. State Machine para estados de venta
- **Opción A**: Estados como string con validación ad-hoc en el service.
- **Opción B**: Clase/módulo dedicado (`state_machine.py`) con transiciones explícitas.
- **Decisión**: Opción B. Transiciones explícitas facilitan testing, evitan errores de transición ilegal y documentan el flujo de negocio.
- **Transiciones permitidas**:
  - `en_curso` → `suspendida` (cualquier usuario con permiso de venta)
  - `en_curso` → `cobrada` (cajero/vendedor, con caja abierta y stock suficiente)
  - `suspendida` → `en_curso` (recuperación)
  - `suspendida` → `cobrada` (mismo validaciones que desde en_curso)
  - `cobrada` → `anulada` (solo Admin/Encargado)
  - `anulada` es terminal.

### 2. Atomicidad de stock en el cobro
- **Opción A**: Decrementar stock en tabla `Producto.stock_actual` y luego insertar `MovimientoStock`.
- **Opción B**: Usar transacción ACID que valide stock, decremente `Producto.stock_actual` e inserte `MovimientoStock` dentro de la misma sesión async.
- **Decisión**: Opción B. En SQLAlchemy 2.0 async con `AsyncSession`, el service ejecuta todo dentro de una transacción. Si falla cualquier paso, se hace rollback completo.
- **Validación de stock negativo**: Se consulta `stock_actual` con `SELECT ... FOR UPDATE` (o equivalente optimista) antes de decrementar. Si `stock_actual - cantidad < 0`, se lanza `HTTPException 409` antes de mutar datos.

### 3. Integración con Caja (C-13 no implementado)
- **Opción A**: Esperar a C-13 para implementar ventas.
- **Opción B**: Crear tabla mínima `Caja` + `MovimientoCaja` dentro de C-12 como "forward-compatible stub".
- **Opción C**: No validar caja en C-12 y dejarlo como deuda técnica.
- **Decisión**: Opción B. Creamos migración mínima para `caja` y `movimiento_caja` con los campos esenciales. El service de ventas inserta `MovimientoCaja` tipo `entrada_venta` al cobrar. C-13 extenderá estos modelos con cierre/apertura completo.
- **Justificación**: No podemos cobrar ventas sin registrar el dinero. Es más limpio crear la tabla mínima ahora que acoplar C-12 y C-13 en una sola sesión.

### 4. Integración con Cuenta Corriente (C-14 no implementado)
- **Opción A**: Esperar a C-14.
- **Opción B**: Crear tabla mínima `CuentaCorriente` (movimientos) y generar deuda automática al cobrar con medio `cuenta_corriente`.
- **Decisión**: Opción B. Tabla mínima con campos: `id`, `empresa_id`, `cliente_id`, `tipo` (deuda/pago), `importe`, `saldo_resultante`, `venta_id`, `fecha`. C-14 extenderá con pagos parciales, estado de cuenta, etc.
- **Justificación**: RN-PAGO-02 y RN-CC-01 exigen deuda automática. Sin la tabla, no podemos cumplir la regla.

### 5. Generación de ticket/comprobante
- **Opción A**: Generar PDF server-side (WeasyPrint, ReportLab).
- **Opción B**: Generar HTML imprimible desde frontend.
- **Opción C**: Devolver JSON con datos del ticket y dejar la presentación al frontend.
- **Decisión**: Opción C para v1.0. El backend devuelve un objeto `TicketData` con: empresa, fecha, items, subtotal, descuentos, total, medio de pago. El frontend formatea e imprime vía `window.print()` o genera PDF client-side en iteración futura.

### 6. Precisión decimal
- **Dinero**: `Decimal(12,2)` para subtotal, descuentos, total, precios, importes.
- **Kilos**: `Decimal(12,3)` para `cantidad_kilos`, `stock_actual`, `stock_resultante`.
- **Justificación**: RN-VENT-01 (precios por kilo) y regla dura del proyecto (nunca float para dinero).

## Risks / Trade-offs

- **[Risk]** C-13 y C-14 no están completos; las tablas mínimas creadas en C-12 pueden requerir migraciones adicionales cuando esos changes se implementen.
  - **Mitigation**: Nombrar tablas y columnas exactamente como aparecen en `04_modelo_de_datos.md`. Documentar en `design.md` qué campos son "forward-compatible".
- **[Risk]** Race condition en stock si dos cajeros cobran el mismo producto simultáneamente.
  - **Mitigation**: Usar transacciones ACID con `SERIALIZABLE` o `SELECT FOR UPDATE` en `Producto` al validar stock. Medir performance; si hay contención, evaluar optimistic locking en iteración futura.
- **[Risk]** Anulación de venta requiere reversión de stock, caja y CC. Es compleja y propensa a errores.
  - **Mitigation**: Implementar anulación como transacción que inserta movimientos inversos (entrada de stock por anulación, movimiento de caja negativo, ajuste de CC). Todo dentro de una sesión ACID. Auditoría obligatoria (RN-AUD-01) para trazabilidad.
- **[Risk]** El frontend POS es la UI más compleja del MVP. Puede escapar del scope de una sesión.
  - **Mitigation**: Dividir en componentes atómicos (Cart, ProductScanner, PaymentPanel). Priorizar funcionalidad sobre diseño visual pulido.

## Migration Plan

1. Alembic migration: crear tablas `venta`, `detalle_venta`, `pago_venta`, `caja`, `movimiento_caja`, `cuenta_corriente`.
2. Seed data: no requiere (datos operativos se generan en runtime).
3. Rollback: `alembic downgrade` elimina tablas. No afecta datos de otros módulos.

## Open Questions

1. ¿El superadmin (C-04 pendiente) puede anular ventas de cualquier empresa? → Decisión post-C-04.
2. ¿Se permite venta sin cliente (público general implícito)? → Sí, `cliente_id` nullable. El snapshot de tipo_cliente será `publico_general`.
3. ¿Qué pasa si la caja está abierta pero el cajero que cobra no es el que abrió? → v1.0 permite cualquier cajero de la empresa cobrar en caja abierta. C-13 puede restringir.
