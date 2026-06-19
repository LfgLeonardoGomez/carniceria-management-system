## ADDED Requirements

### Requirement: Administrador puede crear usuarios en su empresa
El sistema SHALL permitir que un usuario con rol Administrador cree nuevos usuarios asociados a su empresa.

#### Scenario: Creación exitosa de usuario
- **WHEN** un Administrador envía POST /usuarios con nombre, apellido, email y rol_id
- **THEN** el sistema crea el usuario con empresa_id del administrador
- **AND** genera una contraseña temporal aleatoria
- **AND** devuelve los datos del usuario incluyendo la contraseña temporal (visible una sola vez)
- **AND** envía un email de bienvenida con instrucciones para cambiar la contraseña

#### Scenario: Email duplicado
- **WHEN** un Administrador intenta crear un usuario con un email que ya existe en el sistema
- **THEN** el sistema responde con HTTP 409 indicando que el email ya está registrado

#### Scenario: Rol inválido
- **WHEN** un Administrador intenta crear un usuario con un rol_id que no existe
- **THEN** el sistema responde con HTTP 422 indicando rol inválido

### Requirement: Administrador puede listar usuarios de su empresa
El sistema SHALL permitir que un Administrador consulte el listado de usuarios de su empresa con soporte de paginación.

#### Scenario: Listado con filtros
- **WHEN** un Administrador envía GET /usuarios?activo=true&skip=0&limit=20
- **THEN** el sistema retorna solo usuarios de su empresa que coincidan con el filtro
- **AND** no incluye usuarios de otras empresas

### Requirement: Administrador puede editar datos de un usuario
El sistema SHALL permitir que un Administrador actualice nombre, apellido, email y rol de un usuario de su empresa.

#### Scenario: Actualización exitosa
- **WHEN** un Administrador envía PUT /usuarios/{id} con datos válidos
- **THEN** el sistema actualiza el usuario
- **AND** responde con los datos actualizados

#### Scenario: Protección del último administrador
- **WHEN** un Administrador intenta cambiar el rol o desactivar al único administrador activo de la empresa
- **THEN** el sistema responde con HTTP 409
- **AND** el mensaje indica que debe existir al menos un administrador activo

### Requirement: Administrador puede desactivar y reactivar usuarios
El sistema SHALL permitir el soft-delete (desactivación) y reactivación de usuarios por un Administrador.

#### Scenario: Desactivación exitosa
- **WHEN** un Administrador envía PATCH /usuarios/{id}/desactivar
- **THEN** el sistema setea activo = false
- **AND** el usuario no puede iniciar sesión

#### Scenario: Reactivación exitosa
- **WHEN** un Administrador envía PATCH /usuarios/{id}/reactivar
- **THEN** el sistema setea activo = true
- **AND** el usuario puede iniciar sesión nuevamente

#### Scenario: Usuario autenticado intenta auto-desactivarse
- **WHEN** un Administrador intenta desactivar su propio usuario sin existir otro admin activo
- **THEN** el sistema responde con HTTP 409
