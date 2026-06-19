# dev-environment Specification

## Purpose
TBD - created by archiving change c-01-foundation-setup. Update Purpose after archive.
## Requirements
### Requirement: Docker compose levanta PostgreSQL, backend y frontend
El sistema SHALL proveer un archivo `docker-compose.yml` que levante los tres servicios en una sola red Docker.

#### Scenario: Desarrollador ejecuta docker-compose up
- **WHEN** un desarrollador ejecuta `docker-compose up --build` en la raíz del proyecto
- **THEN** PostgreSQL 14+ está disponible en el puerto 5432
- **AND** el backend FastAPI responde en `http://localhost:8000/health`
- **AND** el frontend React responde en `http://localhost:5173/`

### Requirement: Variables de entorno centralizadas
El sistema SHALL usar archivos `.env` (con templates `.env.example`) para configurar todos los servicios sin hardcodear valores.

#### Scenario: Nuevo desarrollador configura el entorno
- **WHEN** un desarrollador copia `.env.example` a `.env` y ejecuta `docker-compose up`
- **THEN** todos los servicios inician sin errores de configuración
- **AND** la aplicación backend lee `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGIN` y `FRONTEND_URL` desde variables de entorno

