# Delta Spec — seed-data (c-22)

## MODIFIED Requirements

### Requirement: Seed data de categorías de producto sugeridas

El sistema SHALL insertar categorías de producto iniciales para **cada empresa existente** en la base de datos (no como registros globales). Las 5 categorías se crean por empresa: Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros.

#### Scenario: Categorías de producto creadas para cada empresa
- **WHEN** se ejecuta el script de seed data y existe al menos una empresa en `empresa`
- **THEN** existen en `categoria_producto` 5 registros con `empresa_id = <id de la empresa>` y los nombres: Carne vacuna, Carne de cerdo, Pollo, Embutidos, Otros

#### Scenario: Categorías por empresa son idempotentes
- **WHEN** se ejecuta el seed data dos veces consecutivas
- **THEN** no se duplican categorías: cada (empresa_id, nombre) aparece una sola vez

#### Scenario: Nueva empresa recibe sus categorías al re-ejecutar el seed
- **WHEN** se crea una nueva empresa y luego se vuelve a correr el seed
- **THEN** la nueva empresa obtiene sus 5 categorías de producto

## ADDED Requirements

### Requirement: Seed data de permisos RBAC por rol

El sistema SHALL poblar la columna `rol.permisos` (JSON) de cada rol a partir de la `PERMISSION_MATRIX` de `rbac.py`, de modo que el campo refleje exactamente los permisos efectivos del rol.

#### Scenario: Permisos se asignan a todos los roles
- **WHEN** se ejecuta el seed data
- **THEN** los 6 roles (superadmin, admin, encargado, cajero, vendedor, desposte) tienen `permisos IS NOT NULL`

#### Scenario: Formato del JSON de permisos
- **WHEN** se consulta `permisos` del rol admin
- **THEN** es un objeto JSON con recursos como keys y listas de operaciones como values (ej. `{"productos": ["read", "create", "update", "delete"], "desposte": ["read", "create", "update"]}`)

#### Scenario: Seed de permisos es idempotente
- **WHEN** se ejecuta el seed dos veces consecutivas
- **THEN** los permisos no se duplican (se sobreescriben con el valor actual de la matriz)

### Requirement: Seed incluye el rol `desposte`

El sistema SHALL crear el rol `desposte` (UUID determinístico) con permisos limitados a: `desposte:read`, `desposte:create`, `desposte:update`, `productos:read`, `stock:read`. Sin acceso a ventas, caja, clientes, ni administración de empresa.

#### Scenario: Rol desposte existe tras ejecutar el seed
- **WHEN** se ejecuta el seed data
- **THEN** existe un registro en `rol` con `nombre = 'desposte'`
- **AND** su `permisos` JSON contiene `desposte`, `productos` y `stock` con sus respectivas operaciones
