## ADDED Requirements

### Requirement: Kardex inmutable de movimientos
El sistema SHALL registrar todo movimiento de stock en la tabla `MovimientoStock` con los siguientes campos obligatorios: `empresa_id`, `producto_id`, `tipo` (entrada_compra | entrada_desposte | salida_venta | ajuste), `cantidad_kilos` (positivo para entradas, negativo para salidas), `stock_resultante` (snapshot post-movimiento), `referencia_tipo` y `referencia_id` (polimórficos), `fecha`.

#### Scenario: Entrada por compra
- **WHEN** se registra una compra de media res (C-08)
- **THEN** el sistema crea un `MovimientoStock` de tipo `entrada_compra` con `cantidad_kilos` positivo, `referencia_tipo = "compra"`, `referencia_id` igual al ID de la compra, y `stock_resultante` actualizado

#### Scenario: Entrada por desposte
- **WHEN** se finaliza un desposte (C-09)
- **THEN** el sistema crea un `MovimientoStock` de tipo `entrada_desposte` por cada corte, con `cantidad_kilos` positivo, `referencia_tipo = "desposte"`, `referencia_id` igual al ID del desposte, y `stock_resultante` actualizado

#### Scenario: Salida por venta
- **WHEN** se cobra una venta (C-12)
- **THEN** el sistema crea un `MovimientoStock` de tipo `salida_venta` por cada ítem, con `cantidad_kilos` negativo, `referencia_tipo = "venta"`, `referencia_id` igual al ID de la venta, y `stock_resultante` actualizado

### Requirement: Consulta de stock actual
El sistema SHALL proveer un endpoint `GET /stock` que devuelva el stock actual por producto calculado como la suma de `cantidad_kilos` de todos los `MovimientoStock` del producto, filtrado por `empresa_id`.

#### Scenario: Stock de producto con movimientos
- **WHEN** se consulta `GET /stock` autenticado para la empresa A
- **THEN** el sistema devuelve una lista de productos con `producto_id`, `nombre`, `stock_actual` (suma de movimientos), `stock_minimo` y estado (`ok`, `alerta`, `critico`)

#### Scenario: Stock de producto sin movimientos
- **WHEN** un producto no tiene movimientos
- **THEN** su `stock_actual` es `0.000`

### Requirement: Kardex paginado por producto
El sistema SHALL proveer un endpoint `GET /stock/movimientos/{producto_id}` que devuelva el historial completo de movimientos de un producto, ordenado por fecha descendente, con paginación (offset/limit o cursor).

#### Scenario: Consulta de kardex con paginación
- **WHEN** se consulta `GET /stock/movimientos/123?page=1&page_size=20`
- **THEN** el sistema devuelve los 20 movimientos más recientes del producto 123, incluyendo `tipo`, `cantidad_kilos`, `stock_resultante`, `referencia_tipo`, `referencia_id` y `fecha`

#### Scenario: Kardex filtrado por empresa
- **WHEN** un usuario de la empresa A consulta el kardex del producto 123
- **THEN** solo se muestran movimientos donde `empresa_id = A`

### Requirement: Ajuste manual de stock
El sistema SHALL permitir ajustes manuales de stock mediante `POST /stock/ajustes`. Requiere rol `Encargado` o `Administrador`. El body debe incluir `producto_id`, `cantidad_kilos` (positivo o negativo) y `motivo`. Crea un `MovimientoStock` de tipo `ajuste`.

#### Scenario: Ajuste positivo
- **WHEN** un Encargado envía `POST /stock/ajustes` con `producto_id=1`, `cantidad_kilos=5.5`, `motivo="Merma recuperada"`
- **THEN** se crea un movimiento tipo `ajuste` con cantidad `5.5`, stock resultante actualizado, y se devuelve el movimiento creado

#### Scenario: Ajuste negativo permitido
- **WHEN** un Encargado envía ajuste negativo cuyo resultado no deja stock negativo
- **THEN** se crea el movimiento tipo `ajuste` con cantidad negativa

#### Scenario: Ajuste rechazado por rol insuficiente
- **WHEN** un usuario con rol `Cajero` intenta `POST /stock/ajustes`
- **THEN** el sistema responde `403 Forbidden`

### Requirement: Bloqueo de stock negativo
El sistema SHALL bloquear toda operación que resulte en stock negativo para un producto. Aplica a salidas por venta y ajustes negativos.

#### Scenario: Venta bloqueada por stock insuficiente
- **WHEN** se intenta cobrar una venta que requiere 10 kg de un producto que tiene 8 kg de stock
- **THEN** el sistema responde `409 Conflict` con mensaje "Stock insuficiente para el producto X"

#### Scenario: Ajuste negativo bloqueado
- **WHEN** se intenta ajustar -5 kg un producto que tiene 3 kg
- **THEN** el sistema responde `409 Conflict` con mensaje "El ajuste dejaría stock negativo"

### Requirement: Alertas de stock mínimo
El sistema SHALL proveer un endpoint `GET /stock/alertas` que liste productos cuyo `stock_actual <= stock_minimo`, ordenados por stock_actual ascendente.

#### Scenario: Producto en alerta
- **WHEN** un producto tiene `stock_actual = 2.5` y `stock_minimo = 5.0`
- **THEN** aparece en `GET /stock/alertas` con estado `alerta`

#### Scenario: Producto crítico
- **WHEN** un producto tiene `stock_actual = 0` y `stock_minimo > 0`
- **THEN** aparece en `GET /stock/alertas` con estado `critico`

#### Scenario: Sin alertas
- **WHEN** ningún producto tiene stock por debajo del mínimo
- **THEN** `GET /stock/alertas` devuelve lista vacía

### Requirement: Aislamiento multi-tenant
Todo endpoint de stock SHALL filtrar implícitamente por `empresa_id` del usuario autenticado. Ningún usuario puede ver ni modificar stock de otra empresa.

#### Scenario: Consulta aislada
- **WHEN** un usuario de empresa A consulta stock, kardex o alertas
- **THEN** solo se devuelven datos donde `empresa_id = A`

#### Scenario: Intento de acceso cruzado
- **WHEN** un usuario de empresa A intenta consultar movimientos usando un `producto_id` que pertenece a empresa B
- **THEN** el sistema responde `404 Not Found` (no revela existencia del recurso)
