## ADDED Requirements

### Requirement: Medios de pago soportados
El sistema SHALL soportar los medios de pago: efectivo, transferencia, debito, credito, cuenta_corriente.

#### Scenario: Medio de pago válido
- **WHEN** se crea un pago con medio efectivo
- **THEN** el sistema acepta el pago

#### Scenario: Medio de pago inválido
- **WHEN** se crea un pago con medio cheques
- **THEN** el sistema rechaza con error 400

### Requirement: Pago único por venta (v1.0)
El sistema SHALL permitir un único medio de pago por venta en v1.0.

#### Scenario: Un solo pago
- **WHEN** se cobra una venta con medio debito
- **THEN** se crea un único PagoVenta asociado

### Requirement: Generar salida de stock al cobrar
El sistema SHALL generar MovimientoStock tipo salida_venta por cada ítem al pasar una venta a estado cobrada.

#### Scenario: Salida de stock exitosa
- **WHEN** una venta de 2 kg de asado y 1.5 kg de vacio se cobra
- **THEN** se generan dos MovimientoStock tipo salida_venta con cantidades negativas
- **AND** se actualiza stock_actual de cada producto

#### Scenario: Stock insuficiente bloquea cobro
- **WHEN** una venta intenta cobrar más kilos de los disponibles en stock
- **THEN** el sistema rechaza el cobro con error 409
- **AND** la venta permanece en su estado anterior

### Requirement: Integración con caja
El sistema SHALL crear un MovimientoCaja tipo entrada_venta al cobrar una venta, excepto si el medio es cuenta_corriente.

#### Scenario: Movimiento de caja en cobro efectivo
- **WHEN** una venta se cobra con medio efectivo
- **THEN** se crea un MovimientoCaja con tipo entrada_venta, medio efectivo e importe igual al total

#### Scenario: Sin movimiento de caja en CC
- **WHEN** una venta se cobra con medio cuenta_corriente
- **THEN** NO se crea MovimientoCaja

### Requirement: Integración con cuenta corriente
El sistema SHALL generar una deuda automática en CuentaCorriente al cobrar con medio cuenta_corriente.

#### Scenario: Deuda automática por CC
- **WHEN** una venta de total 500.00 se cobra con medio cuenta_corriente
- **THEN** se crea un CuentaCorriente tipo deuda con importe 500.00
- **AND** se actualiza saldo_actual del cliente

#### Scenario: Venta sin cliente no permite CC
- **WHEN** se intenta cobrar una venta sin cliente_id con medio cuenta_corriente
- **THEN** el sistema rechaza con error 400

### Requirement: Caja abierta obligatoria
El sistema SHALL validar que exista una caja abierta para la empresa al cobrar una venta (excepto cuenta_corriente, comportamiento a definir en C-13).

#### Scenario: Cobro sin caja abierta
- **WHEN** se intenta cobrar una venta en efectivo y no hay caja abierta para la empresa
- **THEN** el sistema rechaza con error 409

### Requirement: Precisión en pagos
El sistema SHALL almacenar el importe del pago con exactamente 2 decimales.

#### Scenario: Precisión de pago
- **WHEN** el total de la venta es 123.456
- **THEN** el importe del PagoVenta es 123.46
