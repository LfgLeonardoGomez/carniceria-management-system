## ADDED Requirements

### Requirement: Superadmin puede crear usuarios con rol admin
El sistema SHALL permitir que un usuario con rol `superadmin` cree usuarios con rol `admin` y les asigne cualquier `empresa_id` existente.

#### Scenario: Superadmin crea admin para empresa
- **WHEN** un `superadmin` envía POST `/usuarios` con `rol_id` correspondiente a `admin` y `empresa_id` válido
- **THEN** el sistema crea el usuario con el rol `admin` y la `empresa_id` especificada
- **AND** genera y devuelve una contraseña temporal

#### Scenario: Superadmin crea admin sin empresa
- **WHEN** un `superadmin` envía POST `/usuarios` con `rol_id` correspondiente a `admin` y sin `empresa_id`
- **THEN** el sistema crea el usuario con rol `admin` y `empresa_id = NULL`
- **AND** genera y devuelve una contraseña temporal

### Requirement: Superadmin puede listar todos los usuarios
El sistema SHALL permitir que un `superadmin` liste todos los usuarios del sistema sin restricción de `empresa_id`.

#### Scenario: Listado global de usuarios
- **WHEN** un `superadmin` envía GET `/usuarios`
- **THEN** el sistema devuelve todos los usuarios de todas las empresas, ordenados por `created_at` descendente

## MODIFIED Requirements

### Requirement: Administrador puede crear usuario en su empresa
El sistema SHALL permitir que un usuario con rol `admin` cree un nuevo usuario dentro de la misma empresa, asignando nombre, apellido, email y rol operativo.

#### Scenario: Creación exitosa de usuario operativo
- **WHEN** un `admin` envía POST `/usuarios` con datos válidos y rol permitido (`encargado`, `cajero`, o `vendedor`)
- **THEN** el sistema crea el usuario con `activo = true`, `empresa_id = admin.empresa_id`, genera una contraseña temporal, y devuelve los datos del usuario incluyendo la contraseña temporal en texto plano (una sola vez)

#### Scenario: Admin intenta crear otro admin
- **WHEN** un `admin` envía POST `/usuarios` con `rol_id` correspondiente a `admin`
- **THEN** el sistema responde con HTTP 403 Forbidden indicando que no tiene permiso para crear usuarios con rol `admin`

#### Scenario: Email duplicado
- **WHEN** un `admin` envía POST `/usuarios` con un email que ya existe en la base de datos (activo o inactivo)
- **THEN** el sistema responde con HTTP 409 Conflict indicando que el email ya está registrado

#### Scenario: Rol inválido
- **WHEN** un `admin` envía POST `/usuarios` con un rol que no existe en la matriz RBAC
- **THEN** el sistema responde con HTTP 422 Unprocessable Entity indicando rol inválido

### Requirement: Administrador puede listar usuarios de su empresa
El sistema SHALL permitir que un usuario con rol `admin` liste todos los usuarios de su empresa, incluyendo activos e inactivos, con paginación.

#### Scenario: Listado paginado
- **WHEN** un `admin` envía GET `/usuarios` con parámetros de paginación
- **THEN** el sistema devuelve la lista de usuarios de la misma empresa, excluyendo el campo `contrasena_hash`, ordenados por `created_at` descendente

#### Scenario: Usuario no administrador intenta listar
- **WHEN** un usuario con rol distinto a `admin` o `superadmin` envía GET `/usuarios`
- **THEN** el sistema responde con HTTP 403 Forbidden

### Requirement: Administrador puede editar datos de un usuario
El sistema SHALL permitir que un `admin` actualice nombre, apellido, email, rol y estado activo de cualquier usuario de su empresa, excepto cambiar el rol a `admin` o `superadmin`.

#### Scenario: Edición exitosa
- **WHEN** un `admin` envía PATCH `/usuarios/{id}` con datos válidos de un usuario de su empresa
- **THEN** el sistema actualiza el usuario y devuelve el objeto actualizado

#### Scenario: Edición de email duplicado
- **WHEN** un `admin` envía PATCH `/usuarios/{id}` con un email que pertenece a otro usuario
- **THEN** el sistema responde con HTTP 409 Conflict

#### Scenario: Admin intenta elevar rol a admin
- **WHEN** un `admin` envía PATCH `/usuarios/{id}` con `rol_id` correspondiente a `admin`
- **THEN** el sistema responde con HTTP 403 Forbidden

### Requirement: Sistema protege al último Administrador activo
El sistema SHALL impedir que el último usuario con rol `admin` y `activo = true` de una empresa sea desactivado o cambiado de rol.

#### Scenario: Desactivación del último admin bloqueada
- **WHEN** un `admin` intenta desactivar (PATCH `activo = false`) al único usuario con rol `admin` activo de la empresa
- **THEN** el sistema responde con HTTP 409 Conflict indicando que debe existir al menos un `admin` activo

#### Scenario: Cambio de rol del último admin bloqueado
- **WHEN** un `admin` intenta cambiar el rol del único usuario con rol `admin` activo de la empresa
- **THEN** el sistema responde con HTTP 409 Conflict indicando que debe existir al menos un `admin` activo

### Requirement: Administrador puede reactivar usuario inactivo
El sistema SHALL permitir que un `admin` reactive un usuario previamente desactivado (`activo = true`).

#### Scenario: Reactivación exitosa
- **WHEN** un `admin` envía PATCH `/usuarios/{id}` con `activo = true` sobre un usuario inactivo de su empresa
- **THEN** el sistema reactiva el usuario y permite nuevamente el login con las credenciales anteriores

### Requirement: Usuario inactivo no puede iniciar sesión
El sistema SHALL rechazar el login de un usuario cuyo campo `activo` sea `false`.

#### Scenario: Login de usuario desactivado
- **WHEN** un usuario inactivo envía POST `/auth/login` con credenciales válidas
- **THEN** el sistema responde con HTTP 401 Unauthorized indicando que la cuenta está deshabilitada
