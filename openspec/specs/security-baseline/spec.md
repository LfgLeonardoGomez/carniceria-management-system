# security-baseline Specification

## Purpose
TBD - created by archiving change c-01-foundation-setup. Update Purpose after archive.
## Requirements
### Requirement: CORS configurado para el frontend
El sistema SHALL configurar CORS permitiendo únicamente el origen del frontend.

#### Scenario: Petición desde frontend permitida
- **WHEN** el frontend en `http://localhost:5173` realiza una petición al backend
- **THEN** el backend responde con headers CORS apropiados (`Access-Control-Allow-Origin`)
- **AND** las peticiones preflight OPTIONS son respondidas correctamente

#### Scenario: Petición desde origen no permitido es rechazada
- **WHEN** se realiza una petición desde un origen no configurado en `CORS_ORIGIN`
- **THEN** el navegador bloquea la petición por política CORS

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

