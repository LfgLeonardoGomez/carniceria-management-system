## ADDED Requirements

### Requirement: Crear venta con carrito
El sistema SHALL permitir crear una venta con un carrito de ítems, cliente opcional, descuentos y medio de pago.

#### Scenario: Venta con cliente y carrito
- **WHEN** un usuario autenticado envía POST /ventas con cliente_id, items y medio_pago
- **THEN** el sistema crea la venta en estado en_curso con subtotal y total calculados

#### Scenario: Venta sin cliente (público general)
- **WHEN** un usuario autenticado envía POST /ventas sin cliente_id
- **THEN** el sistema crea la venta con cliente_id null y tipo_cliente_al_momento = publico_general

### Requirement: Calcular subtotal y total
El sistema SHALL calcular el subtotal como la suma de los importes de los ítems y el total como subtotal menos descuentos.

#### Scenario: Cálculo con descuento
- **WHEN** una venta tiene ítems con importes 100.00 y 50.00, y descuentos 10.00
- **THEN** el subtotal es 150.00 y el total es 140.00

### Requirement: Precio automático según tipo de cliente
El sistema SHALL seleccionar el precio_unitario automáticamente según el tipo de cliente al momento de la venta.

#### Scenario: Cliente público general
- **WHEN** el tipo de cliente es publico_general
- **THEN** el precio_unitario aplicado es precio_publico del producto

#### Scenario: Cliente mayorista
- **WHEN** el tipo de cliente es mayorista
- **THEN** el precio_unitario aplicado es precio_mayorista del producto

#### Scenario: Cliente especial
- **WHEN** el tipo de cliente es especial
- **THEN** el precio_unitario aplicado es precio_publico del producto (v1.0)

### Requirement: Snapshot de tipo de cliente
El sistema SHALL almacenar el tipo_cliente_al_momento como snapshot en la venta para preservar el historial.

#### Scenario: Snapshot preservado
- **WHEN** se crea una venta para un cliente mayorista
- **THEN** el campo tipo_cliente_al_momento de la venta es mayorista, aunque el cliente cambie su tipo posteriormente

### Requirement: Carrito con productos válidos
El sistema SHALL validar que cada ítem del carrito tenga producto_id existente, cantidad_kilos > 0 y precio_unitario >= 0.

#### Scenario: Producto inexistente
- **WHEN** un ítem del carrito tiene producto_id que no existe en la empresa
- **THEN** el sistema rechaza la venta con error 400

#### Scenario: Cantidad negativa o cero
- **WHEN** un ítem del carrito tiene cantidad_kilos <= 0
- **THEN** el sistema rechaza la venta con error 400

### Requirement: Precisión decimal
El sistema SHALL usar precisión de 2 decimales para dinero y 3 decimales para kilos.

#### Scenario: Precisión de kilos en venta
- **WHEN** se vende 1.234 kg de un producto
- **THEN** la cantidad_kilos almacenada es exactamente 1.234

#### Scenario: Precisión de dinero en total
- **WHEN** el total calculado es 123.456
- **THEN** el total almacenado es 123.46 (redondeo a 2 decimales)
