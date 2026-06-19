## ADDED Requirements

### Requirement: Usuario autenticado puede consultar su perfil
El sistema SHALL exponer un endpoint `GET /usuarios/me` que devuelva los datos del usuario autenticado sin requerir permisos de administrador.

#### Scenario: Consulta de perfil propio
- **WHEN** cualquier usuario autenticado envía GET `/usuarios/me`
- **THEN** el sistema devuelve los datos del usuario (`id`, `email`, `nombre`, `apellido`, `rol`, `empresa_id`, `activo`, `ultimo_acceso`, `created_at`, `updated_at`) excluyendo `contrasena_hash`

### Requirement: Usuario autenticado puede editar su perfil
El sistema SHALL permitir que cualquier usuario autenticado modifique su nombre, apellido y contraseña mediante `PATCH /usuarios/me`, sin afectar otros campos como rol o empresa.

#### Scenario: Edición de nombre y apellido
- **WHEN** un usuario autenticado envía PATCH `/usuarios/me` con `nombre` y `apellido` válidos
- **THEN** el sistema actualiza solo esos campos y devuelve el perfil actualizado

#### Scenario: Cambio de contraseña propia
- **WHEN** un usuario autenticado envía PATCH `/usuarios/me` con `contrasena_actual` y `contrasena_nueva` válidas
- **THEN** el sistema valida que `contrasena_actual` coincida con el hash almacenado, actualiza el hash con `contrasena_nueva`, y devuelve el perfil actualizado

#### Scenario: Cambio de contraseña con contraseña actual incorrecta
- **WHEN** un usuario autenticado envía PATCH `/usuarios/me` con `contrasena_actual` incorrecta
- **THEN** el sistema responde con HTTP 400 Bad Request indicando que la contraseña actual no coincide

#### Scenario: Intento de modificar rol o empresa desde perfil
- **WHEN** un usuario autenticado envía PATCH `/usuarios/me` incluyendo `rol` o `empresa_id`
- **THEN** el sistema ignora esos campos (o responde con 422 si se usa `extra='forbid'` en el schema y el campo no está permitido)

### Requirement: Usuario autenticado puede consultar permisos propios
El sistema SHALL incluir en la respuesta de `GET /usuarios/me` la lista de permisos asociados al rol del usuario, para que el frontend pueda adaptar la UI dinámicamente.

#### Scenario: Perfil con permisos
- **WHEN** un usuario autenticado envía GET `/usuarios/me`
- **THEN** la respuesta incluye un campo `permisos` con el array de strings de permisos disponibles para su rol
