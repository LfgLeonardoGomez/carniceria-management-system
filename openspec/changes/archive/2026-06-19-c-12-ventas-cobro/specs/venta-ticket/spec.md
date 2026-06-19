## ADDED Requirements

### Requirement: Generar ticket post-cobro
El sistema SHALL devolver un objeto con los datos del ticket al cobrar una venta exitosamente.

#### Scenario: Ticket con datos completos
- **WHEN** una venta se cobra exitosamente
- **THEN** la respuesta incluye ticket_data con: empresa, fecha, items, subtotal, descuentos, total, medio_de_pago

### Requirement: Datos del ticket
El ticket_data SHALL incluir nombre comercial de la empresa, fecha/hora de la venta, lista de ítems con cantidad y precio unitario, subtotal, descuentos, total y medio de pago.

#### Scenario: Items en ticket
- **WHEN** el ticket_data se genera
- **THEN** cada ítem contiene nombre del producto, cantidad_kilos, precio_unitario e importe

### Requirement: Placeholder de impresión
En v1.0 el ticket es un JSON imprimible; no se genera PDF ni HTML server-side.

#### Scenario: Respuesta JSON imprimible
- **WHEN** el frontend recibe la respuesta de cobro
- **THEN** puede formatear el ticket_data para impresión vía window.print()
