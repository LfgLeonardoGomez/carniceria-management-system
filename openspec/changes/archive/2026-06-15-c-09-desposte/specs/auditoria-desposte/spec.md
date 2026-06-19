## ADDED Requirements

### Requirement: Registrar auditoría al finalizar desposte
El sistema SHALL registrar una acción de auditoría "FINALIZAR_DESPOSTE" con snapshot completo del desposte y sus cortes al finalizar.

#### Scenario: Auditoría de desposte finalizado
- **WHEN** se finaliza un desposte exitosamente
- **THEN** el sistema crea un registro en Auditoría con accion="FINALIZAR_DESPOSTE", usuario_id del operador, desposte_id, fecha/hora, y un JSON con snapshot completo del desposte y todos sus cortes

#### Scenario: Snapshot completo
- **WHEN** se finaliza un desposte con 3 cortes
- **THEN** el snapshot JSON incluye: desposte.id, compra_id, fecha, operador_id, rendimiento_total, merma, y para cada corte: tipo_corte, kilos_obtenidos, porcentaje_rendimiento, costo_asignado, costo_final_por_kilo, producto_id

### Requirement: Inmutabilidad de auditoría
El sistema SHALL garantizar que los registros de auditoría no pueden ser modificados ni eliminados.

#### Scenario: Intento de modificación
- **WHEN** cualquier usuario intenta modificar o eliminar un registro de auditoría
- **THEN** el sistema rechaza la operación con error 403

### Requirement: Consultar auditoría de desposte
El sistema SHALL permitir consultar el historial de auditoría filtrado por acción y desposte.

#### Scenario: Filtrar por desposte
- **WHEN** el usuario consulta GET /auditoria?accion=FINALIZAR_DESPOSTE&desposte_id={id}
- **THEN** el sistema devuelve los registros de auditoría correspondientes a ese desposte
