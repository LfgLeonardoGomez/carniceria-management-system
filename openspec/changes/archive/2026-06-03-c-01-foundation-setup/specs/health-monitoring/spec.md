## ADDED Requirements

### Requirement: Health check endpoint básico
El sistema SHALL exponer `GET /health` que retorne estado del servicio backend.

#### Scenario: Health check responde OK
- **WHEN** se realiza un GET a `/health`
- **THEN** responde HTTP 200 con JSON `{ "status": "ok", "service": "basile-api" }`

### Requirement: Health check de base de datos
El sistema SHALL exponer `GET /health/db` que verifique conectividad a PostgreSQL.

#### Scenario: Health check de DB responde OK
- **WHEN** se realiza un GET a `/health/db`
- **THEN** responde HTTP 200 con JSON que incluye `{ "status": "ok", "database": "connected" }`

#### Scenario: Health check de DB responde error
- **WHEN** se realiza un GET a `/health/db` y PostgreSQL no está disponible
- **THEN** responde HTTP 503 con JSON que incluye `{ "status": "error", "database": "unreachable" }`

### Requirement: Logging estructurado en JSON
El sistema SHALL usar logging estructurado en formato JSON para todas las peticiones y errores.

#### Scenario: Logs de request en JSON
- **WHEN** el backend recibe cualquier petición HTTP
- **THEN** se emite un log en formato JSON con: timestamp, método, path, status_code, duración_ms
- **AND** los logs de error incluyen stack trace en el campo `error`
