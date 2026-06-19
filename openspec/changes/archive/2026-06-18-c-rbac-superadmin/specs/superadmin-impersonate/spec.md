## ADDED Requirements

### Requirement: Superadmin puede generar JWT de impersonación
El sistema SHALL permitir que un usuario con rol `superadmin` genere un JWT temporal con rol `admin` y `empresa_id` de cualquier empresa existente.

#### Scenario: Impersonación exitosa
- **WHEN** un `superadmin` envía POST `/soporte/impersonate` con `empresa_id` válido
- **THEN** el sistema genera un access token JWT con `sub = superadmin.id`, `rol = "admin"`, `empresa_id = <target>`, `original_role = "superadmin"`, y duración de 15 minutos
- **AND** registra en tabla `Auditoria` la acción `IMPERSONATE_ADMIN` con `actor_id = superadmin.id` y `target_empresa_id = <target>`
- **AND** no genera un refresh token nuevo

#### Scenario: Impersonación rechazada por rol no superadmin
- **WHEN** un usuario con rol distinto a `superadmin` envía POST `/soporte/impersonate`
- **THEN** el sistema responde con HTTP 403 Forbidden

#### Scenario: Impersonación rechazada por empresa inexistente
- **WHEN** un `superadmin` envía POST `/soporte/impersonate` con `empresa_id` que no existe
- **THEN** el sistema responde con HTTP 404 Not Found

### Requirement: JWT de impersonación contiene claim original_role
El sistema SHALL incluir el claim `original_role` en el payload del JWT de impersonación para permitir al frontend identificar el modo impersonación.

#### Scenario: Decodificación de JWT de impersonación
- **WHEN** el frontend decodifica el JWT recibido de `/soporte/impersonate`
- **THEN** el payload contiene `original_role = "superadmin"` además de `rol = "admin"` y `empresa_id`

### Requirement: Impersonación es auditada obligatoriamente
El sistema SHALL registrar cada generación de token de impersonación en la tabla `Auditoria` con datos del actor, target, timestamp, IP y user agent.

#### Scenario: Registro de auditoría completo
- **WHEN** un `superadmin` solicita impersonación exitosa
- **THEN** el registro de `Auditoria` contiene `action = "IMPERSONATE_ADMIN"`, `actor_id`, `target_empresa_id`, `created_at`, y `details` con IP y user agent
