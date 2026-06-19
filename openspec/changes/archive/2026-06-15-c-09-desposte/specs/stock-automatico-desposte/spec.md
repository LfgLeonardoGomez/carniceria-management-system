## ADDED Requirements

### Requirement: Generar stock al finalizar desposte
El sistema SHALL generar automáticamente un MovimientoStock tipo "entrada_desposte" por cada corte al finalizar un desposte.

#### Scenario: Generación de stock exitosa
- **WHEN** se finaliza un desposte con 3 cortes vinculados a productos
- **THEN** el sistema crea 3 registros MovimientoStock tipo "entrada_desposte" con cantidad_kilos = kilos_obtenidos del corte, referencia_id = desposte.id, referencia_tipo = "desposte", y stock_resultante actualizado

#### Scenario: Corte sin producto vinculado
- **WHEN** se finaliza un desposte con un corte que no tiene producto_id
- **THEN** el sistema NO genera MovimientoStock para ese corte y registra una advertencia en auditoría

#### Scenario: Stock resultante correcto
- **WHEN** un producto tiene stock_actual=50kg y se finaliza un desposte con un corte de 10kg del mismo producto
- **THEN** el MovimientoStock tiene stock_resultante=60kg y el producto.stock_actual se actualiza a 60kg

### Requirement: MovimientoStock vinculado al desposte
El sistema SHALL permitir consultar los movimientos de stock generados por un desposte.

#### Scenario: Consultar movimientos de desposte
- **WHEN** el usuario consulta el desposte finalizado
- **THEN** la respuesta incluye los movimientos de stock generados con tipo, cantidad, fecha y stock_resultante

### Requirement: Transaccionalidad
El sistema SHALL generar los movimientos de stock y actualizar el desposte en una transacción atómica.

#### Scenario: Fallo en generación de stock
- **WHEN** ocurre un error al crear un MovimientoStock durante la finalización
- **THEN** el sistema hace rollback completo: no se crea ningún movimiento, el desposte no se marca como finalizado, y se responde con error 500
