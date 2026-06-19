## MODIFIED Requirements

### Requirement: Seed data de roles del sistema
El sistema SHALL insertar los 4 roles obligatorios del sistema al aplicar los seeds.

#### Scenario: Roles insertados correctamente
- **WHEN** se ejecuta el script de seed data
- **THEN** existen en la tabla `rol` los registros: Administrador, Encargado, Cajero, Vendedor
- **AND** cada rol tiene un `id` estable (UUID determinista o secuencia fija) para referencia en tests

## ADDED Requirements

### Requirement: Seed data crea usuario administrador por defecto
El sistema SHALL crear un usuario Administrador por defecto asociado a la empresa de seed, para garantizar acceso inicial al sistema.

#### Scenario: Usuario admin por defecto creado
- **WHEN** se ejecuta el script de seed data
- **THEN** existe en la tabla `usuario` un registro con rol Administrador
- **AND** su email es un valor conocido y configurable por variable de entorno (default: admin@basile.local)
- **AND** su contraseña es un valor seguro generado o configurable por variable de entorno para entornos de desarrollo
- **AND** está asociado a la empresa creada en el seed

#### Scenario: Seed idempotente no duplica admin
- **WHEN** se ejecuta el seed data dos veces consecutivas
- **THEN** no se crean usuarios duplicados
- **AND** no se lanzan excepciones de violación de constraints únicos
