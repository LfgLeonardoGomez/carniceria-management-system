# Spec — Caja Operaciones (delta)

## ADDED Requirements

### Requirement: Apertura de caja
The system SHALL allow an authorized user (`caja:admin`) to open a caja for their empresa
with an initial cash amount, and SHALL reject opening when another caja is already `abierta`
for that empresa.

#### Scenario: Apertura exitosa
- WHEN an authorized user posts `efectivo_inicial` to `/caja/apertura` and no caja is open
- THEN a new caja is created with `estado="abierta"`, `monto_inicial=efectivo_inicial`,
  `usuario_apertura_id=<user>`, and HTTP 201 is returned.

#### Scenario: Segunda apertura rechazada
- WHEN an authorized user posts to `/caja/apertura` while a caja is already `abierta` for the empresa
- THEN HTTP 409 is returned and no second caja is created.

#### Scenario: Aislamiento multi-tenant en apertura
- WHEN empresa A has an open caja and a user of empresa B posts to `/caja/apertura`
- THEN empresa B's apertura succeeds (its own scope), independent of empresa A.

### Requirement: Movimientos manuales de caja
The system SHALL allow registering manual `retiro` and `ingreso_manual` movements with a
description against the currently open caja of the user's empresa.

#### Scenario: Registrar retiro
- WHEN an authorized user posts a `retiro` with importe and descripción
- THEN a MovimientoCaja `tipo="retiro"` is created with the positive magnitude and descripción.

#### Scenario: Registrar ingreso manual
- WHEN an authorized user posts an `ingreso_manual` with importe and descripción
- THEN a MovimientoCaja `tipo="ingreso_manual"` is created.

#### Scenario: Movimiento sin caja abierta
- WHEN an authorized user posts a movimiento and no caja is open
- THEN HTTP 409 is returned.

### Requirement: Cálculo de caja esperada
The system SHALL compute esperado per medio from the open caja's movements:
`efectivo = monto_inicial + ventas_efectivo + ingresos_manuales − retiros`,
`transferencias = ventas_transferencia`, `tarjetas = ventas_debito + ventas_credito`.

#### Scenario: Esperado con ventas y movimientos
- GIVEN apertura 100.00, ventas efectivo 50.00, ingreso manual 20.00, retiro 30.00
- WHEN esperado is computed
- THEN efectivo_esperado == 140.00.

#### Scenario: Esperado tarjetas suma débito y crédito
- GIVEN ventas débito 80.00 and crédito 120.00
- THEN tarjetas_esperadas == 200.00.

### Requirement: Cierre de caja con diferencias
The system SHALL accept real counted amounts at cierre, compute `diferencia = real − esperado`
per medio and `diferencia_total`, flag significant differences, and mark the caja `cerrada`.

#### Scenario: Cierre sin diferencia
- GIVEN esperado efectivo 140.00, real efectivo 140.00 (others matching)
- WHEN cierre is posted
- THEN diferencia_total == 0.00, `tiene_diferencia` is false, estado == "cerrada".

#### Scenario: Cierre con faltante significativo
- GIVEN esperado efectivo 140.00, real efectivo 130.00
- WHEN cierre is posted
- THEN diferencia_efectivo == -10.00, `diferencia_significativa` is true, estado == "cerrada".

#### Scenario: Cierre sin caja abierta
- WHEN cierre is posted and no caja is open
- THEN HTTP 409 is returned.

### Requirement: Autorización de caja
All caja endpoints SHALL require the `caja:admin` permission.

#### Scenario: Rol sin permiso rechazado
- WHEN a `vendedor` (no `caja:admin`) posts to any caja endpoint
- THEN HTTP 403 is returned.
