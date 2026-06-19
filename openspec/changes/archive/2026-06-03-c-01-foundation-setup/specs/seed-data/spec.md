## ADDED Requirements

### Requirement: Seed data de roles del sistema
El sistema SHALL insertar los 4 roles obligatorios del sistema al aplicar los seeds.

#### Scenario: Roles insertados correctamente
- **WHEN** se ejecuta el script de seed data
- **THEN** existen en la tabla `rol` los registros: Administrador, Encargado, Cajero, Vendedor
- **AND** cada rol tiene un `id` estable (UUID determinista o secuencia fija) para referencia en tests

### Requirement: Seed data de categorías de producto sugeridas
El sistema SHALL insertar categorías de producto iniciales como seed data.

#### Scenario: Categorías de producto insertadas
- **WHEN** se ejecuta el script de seed data
- **THEN** existen en la tabla `categoria_producto` los registros: Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros

### Requirement: Seed data de tipos de corte de desposte
El sistema SHALL insertar los 12 tipos de corte fijos para desposte.

#### Scenario: Tipos de corte insertados
- **WHEN** se ejecuta el script de seed data
- **THEN** existen en la tabla correspondiente (o enum/modelo) los registros: Asado, Vacío, Nalga, Cuadril, Peceto, Bola de lomo, Lomo, Matambre, Costilla, Osobuco, Molida, Otros

### Requirement: Seed data de categorías de gasto
El sistema SHALL insertar las categorías de gasto fijas del sistema.

#### Scenario: Categorías de gasto insertadas
- **WHEN** se ejecuta el script de seed data
- **THEN** existen los registros: Alquiler, Empleados, Luz, Agua, Gas, Internet, Combustible, Impuestos, Mantenimiento, Insumos, Otros

### Requirement: Seed script es idempotente
El sistema SHALL permitir ejecutar el seed script múltiples veces sin duplicar registros.

#### Scenario: Ejecución idempotente
- **WHEN** se ejecuta el seed data dos veces consecutivas
- **THEN** no se crean registros duplicados
- **AND** no se lanzan excepciones de violación de constraints únicos
