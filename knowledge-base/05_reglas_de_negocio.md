# Reglas de Negocio

Cada regla tiene un código único `RN-{DOMINIO}-{NN}` para trazabilidad.

---

## Dominio: Seguridad y Multi-tenancia (RN-SEG)

- **RN-SEG-01**: Cada empresa debe tener información aislada. Una empresa nunca debe visualizar información perteneciente a otra empresa.
  - *Justificación*: Garantiza confidencialidad y evita filtraciones de datos entre competidores o usuarios no autorizados.
- **RN-SEG-02**: Todos los endpoints y consultas a base de datos deben filtrar implícitamente por `empresa_id` del usuario autenticado.
- **RN-SEG-03**: Los usuarios deben autenticarse con email y contraseña. Solo pueden acceder a los datos de su empresa asignada.

---

## Dominio: Autenticación (RN-AU)

- **RN-AU-01**: El login requiere email y contraseña válidos.
- **RN-AU-02**: La recuperación de contraseña se realiza mediante envío de correo electrónico con enlace seguro de un solo uso.
- **RN-AU-03**: El sistema debe soportar 4 roles: Administrador, Encargado, Cajero y Vendedor. Cada rol tiene permisos fijos y no configurables por empresa en v1.0.

---

## Dominio: Productos (RN-PROD)

- **RN-PROD-01**: Todo producto debe tener un PLU único dentro de la empresa.
- **RN-PROD-02**: Todo producto debe tener precio público y precio mayorista (ambos >= 0).
- **RN-PROD-03**: El margen de un producto se calcula como la diferencia entre el precio de venta y el costo por kilo, expresado en porcentaje o valor absoluto.
- **RN-PROD-04**: La importación de productos desde Excel exportado por QUENDRA debe preservar PLU, nombre, categoría y precios.
- **RN-PROD-05**: Un producto puede marcarse como inactivo (`activo = false`) sin eliminarlo, preservando historial.

---

## Dominio: Clientes (RN-CLI)

- **RN-CLI-01**: Todo cliente pertenece a una empresa y no puede ser compartido entre empresas.
- **RN-CLI-02**: El tipo de cliente determina el precio aplicado en la venta: Público General → precio público, Mayorista → precio mayorista, Especial → precio personalizado (no definido en detalle en v1.0).
- **RN-CLI-03**: El saldo actual de cuenta corriente se actualiza automáticamente con cada operación de deuda o pago.
- **RN-CLI-04**: Si un cliente tiene límite de cuenta corriente configurado, el sistema debe alertar o bloquear ventas que excedan dicho límite (comportamiento pendiente de definir en v1.0).

---

## Dominio: Proveedores (RN-PROV)

- **RN-PROV-01**: Todo proveedor pertenece a una empresa y no puede ser compartido.
- **RN-PROV-02**: El historial de compras a un proveedor debe mantenerse completo e inmutable para auditoría.

---

## Dominio: Compras (RN-COMP)

- **RN-COMP-01**: En cada compra de media res, el sistema calcula automáticamente el costo por kilo como `costo_total / peso_total`.
- **RN-COMP-02**: El sistema mantiene y actualiza el costo promedio histórico de compras por proveedor o de forma general.
- **RN-COMP-03**: Una compra puede asociarse a uno o más despostes posteriores.

---

## Dominio: Desposte (RN-DESP)

- **RN-DESP-01**: El desposte se realiza sobre una compra de media res específica.
- **RN-DESP-02**: Se soportan 12 tipos de corte: Asado, Vacío, Nalga, Cuadril, Peceto, Bola de lomo, Lomo, Matambre, Costilla, Osobuco, Molida y Otros.
- **RN-DESP-03**: El rendimiento total se calcula como la suma de kilos obtenidos de todos los cortes del desposte.
- **RN-DESP-04**: La merma se calcula como `peso_total de la compra - rendimiento_total`.
- **RN-DESP-05**: El costo final por kilo de cada corte se calcula como `costo_asignado / kilos_obtenidos`.
- **RN-DESP-06**: Al finalizar un desposte, el sistema genera automáticamente entradas de stock para cada corte obtenido.
- **RN-DESP-07**: El operador que realiza el desposte debe quedar registrado.

---

## Dominio: Stock (RN-STOCK)

- **RN-STOCK-01**: Todo el stock debe administrarse exclusivamente por kilos. No se admite unidad, pieza, caja ni otra unidad de medida.
- **RN-STOCK-02**: Las entradas de stock provienen de compras o despostes.
- **RN-STOCK-03**: Las salidas de stock provienen de ventas o ajustes manuales.
- **RN-STOCK-04**: El stock nunca puede quedar negativo. El sistema debe bloquear ventas que generen stock negativo.
- **RN-STOCK-05**: El kardex debe registrar todo movimiento con fecha, tipo, cantidad y stock resultante.
- **RN-STOCK-06**: El sistema debe alertar cuando un producto alcance o esté por debajo del stock mínimo configurado.
- **RN-STOCK-07**: La valorización del stock puede basarse en costo promedio o último costo (método a definir).

---

## Dominio: Ventas (RN-VENT)

- **RN-VENT-01**: La aplicación debe interpretar etiquetas de balanzas SYSTEL (formato numérico, ej: `2000270048052`), detectando PLU y peso.
- **RN-VENT-02**: Al leer una etiqueta SYSTEL, el sistema debe buscar el producto por PLU, calcular el importe (`peso * precio_unitario`) y agregarlo automáticamente al carrito.
- **RN-VENT-03**: La lectura de balanza debe ser compatible con lectores USB, HID y cualquier dispositivo que funcione como teclado.
- **RN-VENT-04**: Debe existir un campo oculto en la interfaz para captura rápida de códigos sin interferir la UX.
- **RN-VENT-05**: El precio unitario aplicado se selecciona automáticamente según el tipo de cliente: público general → precio público, mayorista → precio mayorista, especial → precio especial (si aplica).
- **RN-VENT-06**: El subtotal de la venta es la suma de los importes de los ítems. El total es `subtotal - descuentos`.
- **RN-VENT-07**: Una venta puede suspenderse (guardarse en estado pendiente) y recuperarse posteriormente.
- **RN-VENT-08**: La venta finalizada genera un ticket/imprimible y actualiza stock, caja y cuenta corriente (según medio de pago).

---

## Dominio: Caja (RN-CAJA)

- **RN-CAJA-01**: La caja debe permitir apertura, cierre y movimientos.
- **RN-CAJA-02**: Al cierre, el sistema debe mostrar diferencias entre caja esperada (calculada por ventas + movimientos) y caja real (ingresada manualmente).
- **RN-CAJA-03**: El control de caja abarca efectivo, transferencias y tarjetas (débito y crédito).
- **RN-CAJA-04**: Solo un usuario con rol Cajero, Encargado o Administrador puede operar caja.

---

## Dominio: Medios de Pago (RN-PAGO)

- **RN-PAGO-01**: Los medios de pago soportados son: Efectivo, Transferencia, Débito, Crédito y Cuenta Corriente.
- **RN-PAGO-02**: Si el medio de pago es Cuenta Corriente, la venta genera automáticamente una deuda en la cuenta corriente del cliente.
- **RN-PAGO-03**: Una venta puede tener múltiples medios de pago (split payment), aunque no está explícitamente especificado en la fuente. **Suposición**: en v1.0 se asume un único medio de pago por venta a menos que se decida lo contrario.

---

## Dominio: Cuentas Corrientes (RN-CC)

- **RN-CC-01**: El sistema debe permitir generar deuda, registrar pagos, consultar historial y saldo por cliente.
- **RN-CC-02**: El estado de cuenta por cliente debe ser exportable o imprimible.
- **RN-CC-03**: Las deudas vencidas deben generar alertas/notificaciones.

---

## Dominio: Gastos (RN-GAST)

- **RN-GAST-01**: Los gastos se categorizan en: Alquiler, Empleados, Luz, Agua, Gas, Internet, Combustible, Impuestos, Mantenimiento, Insumos y Otros.
- **RN-GAST-02**: Todo gasto debe registrar fecha, categoría, descripción, importe y medio de pago.
- **RN-GAST-03**: Los gastos elevados (por encima de un umbral) deben generar alertas. El umbral no está definido en la fuente.

---

## Dominio: Reportes (RN-REP)

- **RN-REP-01**: Los reportes de ventas deben soportar filtros por rango de fechas y cliente.
- **RN-REP-02**: Los formatos de exportación de ventas son: Excel, PDF y CSV.
- **RN-REP-03**: Los datos incluidos en exportación de ventas son: fecha, cliente, productos, kilos vendidos, subtotal, total, medio de pago y ganancia estimada.
- **RN-REP-04**: Los reportes financieros deben agrupar por día, semana, mes y año.
- **RN-REP-05**: Los indicadores financieros incluyen: ventas, costos, gastos, utilidad bruta y utilidad neta.

---

## Dominio: Rentabilidad (RN-RENT)

- **RN-RENT-01**: El margen por producto se calcula en base a precio de venta y costo por kilo.
- **RN-RENT-02**: El margen por corte se calcula en base al costo final del desposte y el precio de venta.
- **RN-RENT-03**: La rentabilidad general se calcula considerando ventas, costos de productos vendidos, gastos operativos y utilidad neta.

---

## Dominio: Auditoría (RN-AUD)

- **RN-AUD-01**: El sistema debe registrar en la tabla `Auditoria`, por cada operación relevante, los siguientes campos: `usuario_id`, `accion`, `entidad_tipo`, `entidad_id`, `payload` (snapshot JSON con método HTTP, path, query, body truncado a 4KB, status code y duración en ms), `fecha`, `hora` y `empresa_id`. La captura la realiza un middleware FastAPI sobre los métodos mutantes (POST, PUT, PATCH, DELETE) exitosos (status 2xx).
- **RN-AUD-02**: Los registros de auditoría son inmutables: el `service` no expone métodos de `update` ni `delete`, y la API sólo expone `GET /auditoria`. Ningún rol, incluido el administrador, puede modificar ni eliminar un registro de auditoría existente. Las inserciones son atómicas con la operación que las origina para garantizar trazabilidad completa.

---

## Dominio: Notificaciones (RN-NOTIF)

- **RN-NOTIF-01**: Stock bajo: se genera una notificación de tipo `stock_bajo` cuando el `stock_actual` de un producto es menor o igual a su `stock_minimo` configurable. El trigger se evalúa dentro del mismo flujo de venta o movimiento de stock, garantizando consistencia ACID.
- **RN-NOTIF-02**: Stock crítico: se genera una notificación de tipo `stock_critico` cuando el `stock_actual` de un producto es cero o negativo. Es la alerta de mayor severidad para reposición inmediata.
- **RN-NOTIF-03**: Deudas vencidas: se genera una notificación de tipo `deuda_vencida` cuando una cuenta corriente de cliente tiene saldo deudor y la última transacción supera los `dias_vencimiento` configurados para la empresa. Si la empresa no configuró el umbral, el trigger no se ejecuta (configuración opcional).
- **RN-NOTIF-04**: Gastos elevados: se genera una notificación de tipo `gasto_elevado` cuando se registra un gasto cuyo importe supera el `umbral_gasto` configurado para la empresa. Si la empresa no configuró el umbral, el trigger no se ejecuta.
- **RN-NOTIF-05**: Diferencias de caja: se genera una notificación de tipo `diferencia_caja` cuando al cierre de caja la `diferencia_total` (caja real menos caja esperada) es distinta de cero. La notificación incluye el monto de la diferencia y el identificador del cierre afectado.

---

## Dominio: Excepciones globales

- **RN-GLOBAL-01**: Ningún usuario puede eliminar registros que afecten histórico financiero (ventas cobradas, compras, despostes, movimientos de caja cerrados). Solo se permiten anulaciones con registro de auditoría.
- **RN-GLOBAL-02**: La eliminación física de datos está prohibida; todo cambio destructivo debe ser una baja lógica (`activo = false`) o anulación con trazabilidad.
- **RN-GLOBAL-03**: El sistema no debe mostrar branding de terceros (Base44, frameworks, herramientas de desarrollo) en la interfaz de usuario.
