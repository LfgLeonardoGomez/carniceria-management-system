## ADDED Requirements

### Requirement: Crear desposte
El sistema SHALL permitir crear un desposte vinculado a una compra de media res existente, con fecha y operador.

#### Scenario: Crear desposte exitoso
- **WHEN** un usuario con rol Encargado o Administrador envía POST /despostes con compra_id, fecha y operador_id válidos
- **THEN** el sistema crea un desposte en estado "en_proceso" y devuelve el desposte creado con código 201

#### Scenario: Compra no existe
- **WHEN** el usuario envía compra_id de una compra que no existe o no pertenece a su empresa
- **THEN** el sistema responde con error 404 y mensaje "Compra no encontrada"

#### Scenario: Operador no existe
- **WHEN** el usuario envía operador_id de un usuario que no existe o no pertenece a su empresa
- **THEN** el sistema responde con error 404 y mensaje "Operador no encontrado"

### Requirement: Listar despostes
El sistema SHALL permitir listar despostes de la empresa del usuario autenticado, con filtros opcionales por fecha y estado.

#### Scenario: Listar despostes
- **WHEN** el usuario envía GET /despostes
- **THEN** el sistema devuelve lista paginada de despostes de su empresa con compra, fecha, operador, estado y rendimiento_total

### Requirement: Obtener desposte
El sistema SHALL permitir obtener el detalle completo de un desposte, incluyendo sus cortes.

#### Scenario: Obtener desposte existente
- **WHEN** el usuario envía GET /despostes/{id} de un desposte de su empresa
- **THEN** el sistema devuelve el desposte con todos sus cortes y cálculos

#### Scenario: Desposte no existe
- **WHEN** el usuario envía GET /despostes/{id} de un desposte que no existe o no pertenece a su empresa
- **THEN** el sistema responde con error 404

### Requirement: Finalizar desposte
El sistema SHALL permitir finalizar un desposte en estado "en_proceso", validando que el rendimiento total no exceda el peso de la compra y generando stock automático.

#### Scenario: Finalizar desposte exitoso
- **WHEN** el usuario envía POST /despostes/{id}/finalizar con cortes válidos
- **THEN** el sistema valida rendimiento_total <= peso_total_compra, calcula merma, asigna costos, genera MovimientoStock por cada corte, registra auditoría, cambia estado a "finalizado" y devuelve el desposte completo

#### Scenario: Rendimiento excede peso de compra
- **WHEN** el usuario envía POST /despostes/{id}/finalizar donde rendimiento_total > peso_total_compra
- **THEN** el sistema responde con error 422 y mensaje "El rendimiento total no puede superar el peso de la compra"

#### Scenario: Desposte ya finalizado
- **WHEN** el usuario envía POST /despostes/{id}/finalizar de un desposte ya en estado "finalizado"
- **THEN** el sistema responde con error 409 y mensaje "El desposte ya está finalizado"

#### Scenario: Desposte sin cortes
- **WHEN** el usuario envía POST /despostes/{id}/finalizar de un desposte sin cortes
- **THEN** el sistema responde con error 422 y mensaje "El desposte debe tener al menos un corte"

### Requirement: Estados de desposte
El sistema SHALL manejar dos estados para un desposte: "en_proceso" y "finalizado".

#### Scenario: Estado inicial
- **WHEN** se crea un desposte
- **THEN** su estado es "en_proceso" y no genera stock ni auditoría

#### Scenario: Estado finalizado
- **WHEN** se finaliza un desposte exitosamente
- **THEN** su estado cambia a "finalizado" y no permite modificaciones posteriores
