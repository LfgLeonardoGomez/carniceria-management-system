## ADDED Requirements

### Requirement: Agregar corte a desposte
El sistema SHALL permitir agregar cortes a un desposte en estado "en_proceso", seleccionando tipo de corte, kilos obtenidos y producto destino.

#### Scenario: Agregar corte exitoso
- **WHEN** un usuario envía POST /despostes/{id}/cortes con tipo_corte válido, kilos_obtenidos > 0 y producto_id existente
- **THEN** el sistema crea el corte, recalcula rendimiento_total del desposte y devuelve el corte creado

#### Scenario: Tipo de corte inválido
- **WHEN** el usuario envía tipo_corte que no está en la lista de 12 tipos fijos
- **THEN** el sistema responde con error 422 y mensaje "Tipo de corte no válido"

#### Scenario: Kilos obtenidos negativos o cero
- **WHEN** el usuario envía kilos_obtenidos <= 0
- **THEN** el sistema responde con error 422 y mensaje "Los kilos obtenidos deben ser mayores a cero"

#### Scenario: Desposte finalizado
- **WHEN** el usuario intenta agregar un corte a un desposte en estado "finalizado"
- **THEN** el sistema responde con error 409 y mensaje "No se pueden agregar cortes a un desposte finalizado"

### Requirement: Tipos de corte soportados
El sistema SHALL soportar exactamente 12 tipos de corte: asado, vacio, nalga, cuadril, peceto, bola_de_lomo, lomo, matambre, costilla, osobuco, molida, otros.

#### Scenario: Corte válido
- **WHEN** el usuario envía cualquiera de los 12 tipos de corte
- **THEN** el sistema acepta el corte sin error

### Requirement: Cálculos por corte
El sistema SHALL calcular automáticamente porcentaje_rendimiento, costo_asignado y costo_final_por_kilo para cada corte.

#### Scenario: Cálculos correctos
- **WHEN** un desposte tiene compra con peso_total=100kg y costo_total=$500, y se agrega un corte de 20kg
- **THEN** el sistema calcula porcentaje_rendimiento=20%, costo_asignado=$100, costo_final_por_kilo=$5

#### Scenario: Múltiples cortes
- **WHEN** un desposte tiene 3 cortes de 20kg, 30kg y 10kg sobre una compra de 100kg y $500
- **THEN** el sistema calcula porcentaje_rendimiento 20%, 30%, 10%; costo_asignado $100, $150, $50; costo_final_por_kilo $5, $5, $5 respectivamente

### Requirement: Cálculos agregados del desposte
El sistema SHALL calcular rendimiento_total y merma del desposte automáticamente.

#### Scenario: Rendimiento y merma
- **WHEN** un desposte tiene cortes que suman 85kg sobre una compra de 100kg
- **THEN** el sistema calcula rendimiento_total=85kg y merma=15kg

### Requirement: Unicidad de corte por tipo
El sistema SHALL permitir solo un corte por tipo dentro de un mismo desposte.

#### Scenario: Corte duplicado
- **WHEN** el usuario intenta agregar un segundo corte de tipo "asado" al mismo desposte
- **THEN** el sistema actualiza los kilos del corte existente (upsert) o responde con error 409 según decisión de diseño
