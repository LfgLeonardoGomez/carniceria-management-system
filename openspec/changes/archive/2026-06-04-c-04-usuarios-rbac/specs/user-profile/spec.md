## ADDED Requirements

### Requirement: Usuario autenticado puede consultar su perfil
El sistema SHALL permitir que cualquier usuario autenticado consulte sus propios datos sin requerir permisos de administrador.

#### Scenario: Consulta de perfil propio
- **WHEN** un usuario autenticado envía GET /usuarios/me
- **THEN** el sistema retorna sus datos: id, nombre, apellido, email, rol, empresa, ultimo_acceso
- **AND** no expone el hash de contraseña ni datos internos

### Requirement: Usuario autenticado puede actualizar su perfil
El sistema SHALL permitir que un usuario actualice su nombre, apellido y email.

#### Scenario: Actualización exitosa de perfil
- **WHEN** un usuario envía PUT /usuarios/me con nombre y apellido válidos
- **THEN** el sistema actualiza sus datos
- **AND** responde con el perfil actualizado

#### Scenario: Email duplicado al actualizar perfil
- **WHEN** un usuario intenta cambiar su email a uno que ya pertenece a otro usuario
- **THEN** el sistema responde con HTTP 409 indicando que el email ya está en uso

#### Scenario: Usuario no puede cambiar su propio rol
- **WHEN** un usuario envía PUT /usuarios/me incluyendo un rol_id diferente
- **THEN** el sistema ignora el campo rol_id
- **AND** actualiza solo los campos permitidos
