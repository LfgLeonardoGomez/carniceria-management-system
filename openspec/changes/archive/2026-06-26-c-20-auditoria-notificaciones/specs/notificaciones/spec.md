## ADDED Requirements

### Requirement: Generación automática de notificación por stock bajo
El sistema SHALL generar una notificación de tipo `stock_bajo` cuando el `stock_actual` de un producto sea menor o igual a su `stock_minimo`.

#### Scenario: Stock de producto alcanza mínimo
- **WHEN** un movimiento de stock reduce el `stock_actual` de un producto a un valor menor o igual que `stock_minimo`
- **THEN** el sistema inserta una notificación de tipo `stock_bajo` con `mensaje` descriptivo, `entidad_tipo = 'producto'`, `entidad_id` del producto afectado, y `leida = false`

### Requirement: Generación automática de notificación por stock crítico
El sistema SHALL generar una notificación de tipo `stock_critico` cuando el `stock_actual` de un producto sea menor o igual a cero.

#### Scenario: Stock de producto llega a cero o negativo
- **WHEN** un movimiento de stock reduce el `stock_actual` a 0 o menos
- **THEN** el sistema inserta una notificación de tipo `stock_critico` con `entidad_tipo = 'producto'` y `entidad_id` correspondiente

### Requirement: Generación automática de notificación por diferencia de caja
El sistema SHALL generar una notificación de tipo `diferencia_caja` cuando el cierre de caja registre una `diferencia_total` distinta de cero.

#### Scenario: Cierre de caja con diferencia
- **WHEN** un usuario realiza el cierre de caja y `diferencia_total != 0`
- **THEN** el sistema inserta una notificación de tipo `diferencia_caja` con `entidad_tipo = 'caja'` y `entidad_id` del cierre

### Requirement: Generación automática de notificación por deuda vencida
El sistema SHALL generar una notificación de tipo `deuda_vencida` cuando una cuenta corriente de cliente tenga saldo positivo (deudor) y haya excedido los días de vencimiento configurados por la empresa.

#### Scenario: Deuda de cliente supera días de vencimiento
- **WHEN** se evalúa una cuenta corriente cuyo saldo es mayor a cero y la última transacción tiene más días que el `dias_vencimiento` configurado para la empresa
- **THEN** el sistema inserta una notificación de tipo `deuda_vencida` con `entidad_tipo = 'cuenta_corriente'` y `entidad_id` correspondiente

### Requirement: Generación automática de notificación por gasto elevado
El sistema SHALL generar una notificación de tipo `gasto_elevado` cuando un gasto registrado supere el umbral configurado por la empresa.

#### Scenario: Gasto supera umbral configurado
- **WHEN** un usuario registra un gasto cuyo monto sea mayor al `umbral_gasto` configurado para la empresa
- **THEN** el sistema inserta una notificación de tipo `gasto_elevado` con `entidad_tipo = 'gasto'` y `entidad_id` del gasto

### Requirement: Consulta de notificaciones del usuario autenticado
El sistema SHALL exponer el endpoint `GET /notificaciones` que devuelva las notificaciones de la empresa del usuario autenticado, ordenadas por fecha descendente, con opción de filtrar por `leida`.

#### Scenario: Usuario consulta sus notificaciones no leídas
- **WHEN** un usuario autenticado realiza `GET /notificaciones?leida=false`
- **THEN** el sistema retorna solo las notificaciones de su empresa donde `leida = false`

### Requirement: Marcado de notificación como leída
El sistema SHALL exponer el endpoint `PATCH /notificaciones/{id}/leida` para que el usuario autenticado marque una notificación como leída.

#### Scenario: Usuario marca notificación como leída
- **WHEN** un usuario autenticado realiza `PATCH /notificaciones/{id}/leida`
- **THEN** el sistema actualiza `leida = true` y `fecha_lectura` solo si la notificación pertenece a su empresa

#### Scenario: Usuario intenta marcar notificación de otra empresa
- **WHEN** un usuario intenta marcar como leída una notificación cuyo `empresa_id` no coincide con el suyo
- **THEN** el sistema retorna 404 Not Found

### Requirement: Aislamiento multi-tenant en notificaciones
El sistema SHALL garantizar que las notificaciones de una empresa no sean visibles ni modificables por usuarios de otra empresa.

#### Scenario: Consulta de notificaciones cross-tenant
- **WHEN** un usuario autenticado de la empresa A consulta `GET /notificaciones`
- **THEN** el sistema retorna únicamente notificaciones donde `empresa_id` corresponde a la empresa A
