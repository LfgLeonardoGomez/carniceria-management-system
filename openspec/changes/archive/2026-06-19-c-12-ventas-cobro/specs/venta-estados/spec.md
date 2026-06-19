## ADDED Requirements

### Requirement: Estados de venta
El sistema SHALL soportar los estados de venta: en_curso, suspendida, cobrada, anulada.

#### Scenario: Estados definidos
- **WHEN** se consulta el modelo de venta
- **THEN** los estados válidos son en_curso, suspendida, cobrada, anulada

### Requirement: Transiciones controladas de estado
El sistema SHALL permitir solo las transiciones de estado definidas por la máquina de estados.

#### Scenario: Suspender venta en curso
- **WHEN** una venta está en estado en_curso
- **THEN** un usuario con permiso puede cambiarla a suspendida

#### Scenario: Cobrar venta en curso
- **WHEN** una venta está en estado en_curso
- **THEN** un cajero puede cambiarla a cobrada si pasa todas las validaciones

#### Scenario: Recuperar venta suspendida
- **WHEN** una venta está en estado suspendida
- **THEN** un cajero puede cambiarla a en_curso

#### Scenario: Cobrar venta suspendida
- **WHEN** una venta está en estado suspendida
- **THEN** un cajero puede cambiarla a cobrada si pasa todas las validaciones

#### Scenario: Anular venta cobrada
- **WHEN** una venta está en estado cobrada
- **THEN** un usuario con rol Admin o Encargado puede cambiarla a anulada

#### Scenario: Transición ilegal bloqueada
- **WHEN** se intenta cambiar una venta cobrada a suspendida
- **THEN** el sistema rechaza la operación con error 409

#### Scenario: Transición desde anulada bloqueada
- **WHEN** una venta está en estado anulada
- **THEN** ninguna transición es permitida (estado terminal)

### Requirement: Suspensión de venta
El sistema SHALL permitir suspender una venta en_curso, preservando el carrito y datos para recuperación posterior.

#### Scenario: Suspender y recuperar
- **WHEN** un cajero suspende una venta en_curso
- **THEN** la venta queda en estado suspendida con todos sus ítems intactos
- **AND** posteriormente puede recuperarse por su ID

### Requirement: Anulación con reversión
El sistema SHALL revertir stock, caja y cuenta corriente al anular una venta cobrada.

#### Scenario: Anulación reversión completa
- **WHEN** un Admin anula una venta cobrada con medio efectivo y cliente con CC
- **THEN** el sistema genera entrada de stock de anulación
- **AND** genera movimiento de caja negativo
- **AND** si el medio era cuenta_corriente, ajusta el saldo del cliente
- **AND** registra auditoría de la anulación

#### Scenario: Anulación sin permisos
- **WHEN** un cajero intenta anular una venta cobrada
- **THEN** el sistema rechaza con error 403

### Requirement: Consulta de ventas por estado
El sistema SHALL permitir listar ventas filtradas por estado y empresa.

#### Scenario: Listar ventas suspendidas
- **WHEN** un cajero consulta GET /ventas?estado=suspendida
- **THEN** el sistema retorna solo las ventas suspendidas de su empresa
