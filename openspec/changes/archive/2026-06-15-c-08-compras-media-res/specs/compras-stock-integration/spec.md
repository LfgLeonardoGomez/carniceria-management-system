## ADDED Requirements

### Requirement: Al crear compra se genera entrada automática de stock
El sistema SHALL generar automáticamente un `MovimientoStock` tipo `entrada_compra` al crear una compra de media res. El movimiento SHALL vincularse a la compra mediante `referencia_id` y `referencia_tipo`. El movimiento SHALL actualizar el `stock_resultante` del producto "Media Res" de la empresa.

#### Scenario: Entrada de stock al crear compra
- **WHEN** el sistema crea una compra con `peso_total = 150.500`
- **THEN** el sistema genera un `MovimientoStock` con `tipo = entrada_compra`, `cantidad_kilos = 150.500`, `referencia_tipo = compra`, `referencia_id = <id_compra>`, y `stock_resultante` refleja la suma al stock previo

#### Scenario: Producto "Media Res" no existe y se crea automáticamente
- **WHEN** el sistema crea la primera compra de una empresa y no existe producto con `plu = "MEDIA_RES"`
- **THEN** el sistema crea automáticamente un producto con `nombre = "Media Res"`, `plu = "MEDIA_RES"`, `stock_actual = 0`, y luego genera el movimiento de stock

#### Scenario: Stock resultante es correcto tras múltiples compras
- **WHEN** una empresa tiene stock de 200.000 kg de Media Res y se registra una nueva compra de 150.500 kg
- **THEN** el movimiento de stock tiene `stock_resultante = 350.500` y el producto actualiza `stock_actual = 350.500`

### Requirement: Al anular compra se genera salida de stock inversa
El sistema SHALL generar un `MovimientoStock` tipo `salida_venta` (o `ajuste`) con cantidad negativa al anular una compra, revirtiendo el stock agregado. El stock resultante nunca SHALL ser negativo (RN-STOCK-04).

#### Scenario: Reversión de stock al anular compra
- **WHEN** una compra de 100.000 kg es anulada y el stock actual de Media Res es 250.000 kg
- **THEN** el sistema genera un movimiento con `cantidad_kilos = -100.000` y `stock_resultante = 150.000`

#### Scenario: Anulación bloqueada si stock insuficiente
- **WHEN** una compra de 100.000 kg es anulada pero el stock actual de Media Res es 50.000 kg
- **THEN** el sistema devuelve 409 Conflict con mensaje "Stock insuficiente para anular la compra"

### Requirement: Movimiento de stock es auditado y trazable
El sistema SHALL registrar el `usuario_id` que generó el movimiento de stock en el campo `operador_id` (o equivalente) del `MovimientoStock`. El sistema SHALL garantizar que todo movimiento de stock tenga `empresa_id` y `producto_id` válidos.

#### Scenario: Movimiento de stock tiene operador identificado
- **WHEN** el usuario con ID `user-123` crea una compra
- **THEN** el `MovimientoStock` generado tiene `operador_id = user-123`

#### Scenario: Movimiento de stock vinculado a compra es consultable
- **WHEN** un usuario consulta el kardex del producto "Media Res"
- **THEN** el movimiento de entrada aparece con `referencia_tipo = compra` y `referencia_id` coincidente
