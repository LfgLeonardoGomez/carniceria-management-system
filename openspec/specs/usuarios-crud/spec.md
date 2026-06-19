# Purpose

TBD: Define the purpose of the usuarios-crud capability.

## Requirements

### Requirement: Administrador puede crear usuario en su empresa
El sistema SHALL permitir que un usuario con rol Administrador cree un nuevo usuario dentro de la misma empresa, asignando nombre, apellido, email y rol.

#### Scenario: Creación exitosa de usuario
- **WHEN** un Administrador envía POST `/usuarios` con datos válidos y rol permitido
- **THEN** el sistema crea el usuario con `activo = true`, genera una contraseña temporal, almacena el hash de la contraseña, y devuelve los datos del usuario incluyendo la contraseña temporal en texto plano (una sola vez)

#### Scenario: Email duplicado
- **WHEN** un Administrador envía POST `/usuarios` con un email que ya existe en la base de datos (activo o inactivo)
- **THEN** el sistema responde con HTTP 409 Conflict indicando que el email ya está registrado

#### Scenario: Rol inválido
- **WHEN** un Administrador envía POST `/usuarios` con un rol que no existe en la matriz RBAC
- **THEN** el sistema responde con HTTP 422 Unprocessable Entity indicando rol inválido

### Requirement: Administrador puede listar usuarios de su empresa
El sistema SHALL permitir que un usuario con rol Administrador liste todos los usuarios de su empresa, incluyendo activos e inactivos, con paginación.

#### Scenario: Listado paginado
- **WHEN** un Administrador envía GET `/usuarios` con parámetros de paginación
- **THEN** el sistema devuelve la lista de usuarios de la misma empresa, excluyendo el campo `contrasena_hash`, ordenados por `created_at` descendente

#### Scenario: Usuario no administrador intenta listar
- **WHEN** un usuario con rol distinto a Administrador envía GET `/usuarios`
- **THEN** el sistema responde con HTTP 403 Forbidden

### Requirement: Administrador puede editar datos de un usuario
El sistema SHALL permitir que un Administrador actualice nombre, apellido, email, rol y estado activo de cualquier usuario de su empresa.

#### Scenario: Edición exitosa
- **WHEN** un Administrador envía PATCH `/usuarios/{id}` con datos válidos
- **THEN** el sistema actualiza el usuario y devuelve el objeto actualizado

#### Scenario: Edición de email duplicado
- **WHEN** un Administrador envía PATCH `/usuarios/{id}` con un email que pertenece a otro usuario
- **THEN** el sistema responde con HTTP 409 Conflict

### Requirement: Sistema protege al último Administrador activo
El sistema SHALL impedir que el último usuario con rol Administrador y `activo = true` de una empresa sea desactivado o cambiado de rol.

#### Scenario: Desactivación del último admin bloqueada
- **WHEN** un Administrador intenta desactivar (PATCH `activo = false`) al único usuario con rol Administrador activo de la empresa
- **THEN** el sistema responde con HTTP 409 Conflict indicando que debe existir al menos un Administrador activo

#### Scenario: Cambio de rol del último admin bloqueado
- **WHEN** un Administrador intenta cambiar el rol del único usuario con rol Administrador activo de la empresa
- **THEN** el sistema responde con HTTP 409 Conflict indicando que debe existir al menos un Administrador activo

### Requirement: Administrador puede reactivar usuario inactivo
El sistema SHALL permitir que un Administrador reactive un usuario previamente desactivado (`activo = true`).

#### Scenario: Reactivación exitosa
- **WHEN** un Administrador envía PATCH `/usuarios/{id}` con `activo = true` sobre un usuario inactivo
- **THEN** el sistema reactiva el usuario y permite nuevamente el login con las credenciales anteriores

### Requirement: Usuario inactivo no puede iniciar sesión
El sistema SHALL rechazar el login de un usuario cuyo campo `activo` sea `false`.

#### Scenario: Login de usuario desactivado
- **WHEN** un usuario inactivo envía POST `/auth/login` con credenciales válidas
- **THEN** el sistema responde con HTTP 401 Unauthorized indicando que la cuenta está deshabilitada
