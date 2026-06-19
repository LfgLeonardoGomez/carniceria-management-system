## ADDED Requirements

### Requirement: Superadmin puede asignar admin a empresa
El sistema SHALL permitir que un `superadmin` asigne un usuario con rol `admin` a una empresa mediante el campo `admin_id` de la tabla `empresa`.

#### Scenario: Asignación exitosa de admin
- **WHEN** un `superadmin` envía PATCH `/empresas/{id}` con `admin_id` de un usuario que tiene rol `admin`
- **THEN** el sistema actualiza `empresa.admin_id` y devuelve la empresa actualizada
- **AND** el usuario asignado mantiene su `empresa_id` igual al de la empresa

#### Scenario: Asignación rechazada por usuario no admin
- **WHEN** un `superadmin` envía PATCH `/empresas/{id}` con `admin_id` de un usuario cuyo rol no es `admin`
- **THEN** el sistema responde con HTTP 422 Unprocessable Entity indicando que el usuario debe tener rol `admin`

#### Scenario: Asignación rechazada por rol no superadmin
- **WHEN** un usuario con rol `admin` envía PATCH `/empresas/{id}` con `admin_id`
- **THEN** el sistema responde con HTTP 403 Forbidden

### Requirement: Empresa tiene campo admin_id opcional
El sistema SHALL permitir que `empresa.admin_id` sea NULL hasta que el superadmin asigne un admin.

#### Scenario: Creación de empresa sin admin
- **WHEN** un `superadmin` crea una empresa con POST `/empresas` sin especificar `admin_id`
- **THEN** la empresa se crea con `admin_id = NULL`
- **AND** responde con HTTP 201 Created
