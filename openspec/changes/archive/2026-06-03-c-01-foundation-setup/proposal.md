# Proposal: C-01 Foundation Setup

## Why

BASILE es un SaaS multiempresa para gestión integral de carnicerías. Antes de implementar cualquier funcionalidad de negocio (auth, ventas, stock, desposte), es necesario establecer una base técnica sólida que permita desarrollo paralelo, despliegue reproducible y testing confiable. Sin esta fundación, cada change posterior arrastra deuda técnica y riesgo de inconsistencia entre entornos.

## What Changes

- **Scaffolding completo del proyecto** siguiendo la estructura de directorios propuesta en `08_arquitectura_propuesta.md` §Estructura de directorios, adaptada al stack FastAPI + React SPA.
- **Docker + docker-compose** para desarrollo local: PostgreSQL 14+, backend Python (FastAPI), frontend React (Vite).
- **Backend FastAPI** con async/await, inyección de dependencias, Pydantic `BaseModel` con `extra='forbid'`, organización por dominios (`modules/`).
- **Frontend React SPA** con TypeScript `strict: true`, Vite, Zustand para estado global, estructura por features.
- **Base de datos PostgreSQL** con SQLModel/SQLAlchemy 2.0, pool de conexiones async, RLS preparado (activado en tablas de negocio).
- **Alembic** configurado para migraciones automáticas y manuales.
- **Tablas iniciales**: `empresa`, `rol`, `usuario` (schema mínimo para habilitar C-02 auth-core).
- **Seed data obligatorio**: roles del sistema (Administrador, Encargado, Cajero, Vendedor), categorías de producto sugeridas, tipos de corte de desposte, categorías de gasto.
- **Variables de entorno documentadas**: `.env` templates para backend y frontend con todas las variables requeridas por el sistema.
- **Seguridad base**: CORS configurado, rate limiting en endpoints de auth (preparado para C-02), logging estructurado (JSON).
- **Health check endpoints**: `/health` y `/health/db` para verificar estado del sistema y conectividad a base de datos.
- **CI/CD pipeline skeleton**: GitHub Actions con jobs de lint, type-check y test (backend + frontend).

## Capabilities

### New Capabilities
- `dev-environment`: Docker compose para desarrollo local con PostgreSQL, backend y frontend.
- `backend-foundation`: Scaffolding de FastAPI con estructura por dominios, async DB, Pydantic strict.
- `frontend-foundation`: Scaffolding de React SPA con TypeScript strict, Vite, Zustand, estructura por features.
- `database-foundation`: Conexión PostgreSQL con SQLModel/SQLAlchemy 2.0, Alembic configurado, tablas iniciales (`empresa`, `rol`, `usuario`).
- `seed-data`: Seeders para roles, categorías de producto, tipos de corte, categorías de gasto.
- `health-monitoring`: Endpoints de health check y logging estructurado.
- `security-baseline`: CORS, rate limiting preparado, headers de seguridad base.

### Modified Capabilities
- *(ninguno — este es el primer change del proyecto)*

## Impact

- **Nuevo repositorio estructurado**: Se crean los directorios `backend/`, `frontend/`, `docker-compose.yml`, `.env` templates.
- **Dependencias nuevas**: FastAPI, SQLModel, Alembic, psycopg (async), React 18, Vite, Zustand, TypeScript strict.
- **Base de datos**: Se requiere PostgreSQL 14+ en desarrollo y test.
- **Desbloquea**: Todo el resto del sistema. C-01 es el único change sin prerequisitos y habilita C-02 (auth-core) y C-03 (empresa-config).
- **Governance**: CRÍTICO — cualquier error aquí se propaga a los 19 changes restantes.
