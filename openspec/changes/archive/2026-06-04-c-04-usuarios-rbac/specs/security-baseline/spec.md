## MODIFIED Requirements

### Requirement: Rate limiting preparado en auth
El sistema SHALL tener configurado rate limiting en los endpoints de autenticación (preparado para C-02).

#### Scenario: Rate limiting en login
- **WHEN** se inspecciona la configuración de middleware o dependencias del router de auth
- **THEN** existe una dependencia o middleware de rate limiting configurado para los endpoints `/auth/*`
- **AND** la configuración permite 5 intentos por ventana de 60 segundos por IP+email

### Requirement: Headers de seguridad base
El sistema SHALL incluir headers de seguridad HTTP base (X-Content-Type-Options, X-Frame-Options).

#### Scenario: Headers de seguridad presentes
- **WHEN** se realiza cualquier petición al backend
- **THEN** la respuesta incluye `X-Content-Type-Options: nosniff`
- **AND** incluye `X-Frame-Options: DENY`

## ADDED Requirements

### Requirement: Endpoints protegidos requieren permiso de rol
El sistema SHALL verificar que el rol del usuario autenticado tenga permiso sobre el recurso solicitado, además de validar el token JWT.

#### Scenario: Endpoint de empresa requiere rol Administrador
- **WHEN** un usuario con rol Cajero envía una petición a /empresas/me
- **THEN** el sistema responde con HTTP 403 Forbidden
- **AND** el mensaje indica permiso insuficiente

#### Scenario: Endpoint de usuarios requiere rol Administrador
- **WHEN** un usuario con rol Encargado envía una petición a /usuarios
- **THEN** el sistema responde con HTTP 403 Forbidden

#### Scenario: Endpoint de stock requiere rol Encargado o superior
- **WHEN** un usuario con rol Vendedor envía una petición a /stock/ajustes
- **THEN** el sistema responde con HTTP 403 Forbidden
