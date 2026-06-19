## Context

BASILE es un SaaS multiempresa para carnicerías. Este change (C-01) es la fundación sobre la cual se construyen los 19 changes restantes. El proyecto hereda reglas del `AGENTS.md` global y específicas de BASILE: async/await obligatorio en I/O-bound, Pydantic strict, TypeScript `strict: true`, multi-tenancia por `empresa_id`, y TDD obligatorio para toda lógica de negocio.

Estado actual: el proyecto tiene `knowledge-base/`, `CHANGES.md`, `AGENTS.md` y `README.md`. No existe código fuente, ni configuración de infraestructura, ni base de datos.

## Goals / Non-Goals

**Goals:**
1. Tener un entorno de desarrollo local reproducible con un solo comando (`docker-compose up`).
2. Scaffolding del backend (FastAPI) y frontend (React SPA) con estructura por dominio/features.
3. Conexión a PostgreSQL con SQLModel/SQLAlchemy 2.0 async, Alembic configurado.
4. Schema inicial mínimo: `empresa`, `rol`, `usuario` (habilita C-02 auth-core).
5. Seed data del sistema: roles, categorías de producto, tipos de corte, categorías de gasto.
6. Health check endpoints (`/health`, `/health/db`).
7. Logging estructurado (JSON) y CORS configurado.
8. Pipeline CI/CD skeleton (lint, type-check, test).

**Non-Goals:**
- Implementación de login/logout (C-02).
- CRUD completo de empresa (C-03).
- Frontend funcional con pantallas (solo scaffolding y routing base).
- Despliegue a producción (solo local dev + CI skeleton).
- RLS activo con políticas complejas (se prepara el campo pero las políticas detalladas vienen en changes posteriores).

## Decisions

### D-01 — FastAPI + SQLModel en lugar de Django o NestJS
**Decisión**: Backend en FastAPI (Python) con SQLModel como ORM principal.
**Rationale**: FastAPI ofrece async/await nativo, auto-generación de OpenAPI, y Pydantic integrado — todo alineado con las reglas duras del proyecto. SQLModel combina SQLAlchemy 2.0 con Pydantic, reduciendo boilerplate de modelos. Django es síncrono por defecto y más opinionado; NestJS requiere Node.js y el proyecto ya define Python en el stack.
**Alternativas consideradas**: Django + Django REST, NestJS + TypeORM.

### D-02 — React SPA con Vite en lugar de Next.js
**Decisión**: React 18 SPA con Vite como build tool.
**Rationale**: El sistema no requiere SSR (es una aplicación de gestión interna, no pública). Vite ofrece HMR rápido y configuración mínima. Next.js agrega complejidad innecesaria para un SPA. Zustand cubre el estado global sin la verbosidad de Redux.
**Alternativas consideradas**: Next.js (App Router), Vue 3 + Vite, SvelteKit.

### D-03 — psycopg (async) en lugar de asyncpg directo
**Decisión**: Usar `psycopg[binary,pool]` (versión 3.x) como driver async de PostgreSQL.
**Rationale**: SQLAlchemy 2.0 recomienda `psycopg` como driver moderno para Python 3.10+. Soporta async nativamente y es el sucesor de `psycopg2`. `asyncpg` es más rápido pero requiere capa de compatibilidad con SQLAlchemy.
**Alternativas consideradas**: `asyncpg` + `sqlalchemy-asyncpg`.

### D-04 — Alembic para migraciones en lugar de migrations manuales
**Decisión**: Alembic como framework de migraciones.
**Rationale**: Es el estándar de facto para SQLAlchemy. Permite generar migraciones automáticas desde modelos y ejecutarlas en orden. En tests de integración se usará `create_all` + drop para velocidad, pero en dev/prod las migraciones son obligatorias.
**Alternativas consideradas**: Migraciones manuales en SQL puro, Liquibase.

### D-05 — Docker compose para local dev en lugar de instancias locales
**Decisión**: Un único `docker-compose.yml` para levantar PostgreSQL, backend y frontend.
**Rationale**: Garantiza que todos los desarrolladores usen la misma versión de PostgreSQL y las mismas variables de entorno. El backend corre con `uvicorn` en reload y el frontend con `vite --host`.
**Alternativas consideradas**: PostgreSQL local nativo, devcontainers.

### D-06 — Estructura por dominio en backend y por feature en frontend
**Decisión**: Backend organizado en `modules/{dominio}/` (router, service, repository, models). Frontend en `features/{dominio}/` (components, hooks, services, types).
**Rationale**: Alineado con DDD ligero y Clean Architecture. Cada dominio (ventas, stock, desposte) tiene su propia lógica, entidades y reglas. Evita monolitos spaghetti y facilita que múltiples agentes trabajen en paralelo en changes posteriores.
**Alternativas consideradas**: MVC tradicional, organización por tipo de archivo (`controllers/`, `models/`).

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| **R-01** — Configuración de Docker en Windows puede ser lenta o problemática con volúmenes. | Medio | Usar WSL2 backend en Docker Desktop; documentar pasos de troubleshooting en `README.md`. |
| **R-02** — SQLModel es relativamente nuevo; puede tener edge cases con relaciones complejas. | Medio | Fallback a SQLAlchemy 2.0 declarativo puro si SQLModel falla; mantener modelos simples en C-01. |
| **R-03** — Async DB en tests requiere `pytest-asyncio` + `AsyncSession`; curva de aprendizaje. | Bajo | Documentar patrones de test en `backend/tests/conftest.py`; usar `testcontainers` para PostgreSQL real. |
| **R-04** — Seed data puede crecer y ralentizar tests de integración. | Bajo | Separar seeds en "obligatorios del sistema" (roles, categorías) y "demo". Solo los obligatorios corren en tests. |
| **R-05** — TypeScript strict puede rechazar código válido si no se configura bien `tsconfig.json`. | Bajo | Usar `strict: true` desde el inicio; corregir errores en scaffolding, no postergar. |

## Migration Plan

No aplica migración de datos existentes (proyecto nuevo). El plan de despliegue inicial:
1. Clonar repo.
2. Copiar `.env.example` → `.env` y ajustar variables.
3. `docker-compose up --build`.
4. Verificar `http://localhost:8000/health` y `http://localhost:5173/`.
5. Ejecutar `docker-compose exec backend alembic upgrade head` para migraciones.
6. Ejecutar `docker-compose exec backend python -m seeds.run` para seed data.

Rollback: `docker-compose down -v` elimina volúmenes y vuelve a estado limpio.

## Open Questions

1. **Q-01**: ¿Se usará `poetry` o `pip + requirements.txt` para dependencias de Python? → **Decisión tentativa**: `requirements.txt` + `requirements-dev.txt` para simplicidad; evaluar Poetry en C-05 si el árbol de dependencias crece.
2. **Q-02**: ¿Dónde se alojarán logos y exportaciones en dev? → **Decisión tentativa**: volumen Docker `./uploads` mapeado a contenedor backend; en producción se migrará a S3/Cloudinary.
3. **Q-03**: ¿Se requiere `nginx` reverse proxy en dev? → **Decisión tentativa**: no en C-01; se agrega en C-20 o cuando se prepare staging.
4. **Q-04**: ¿Se usa `uvicorn` directo o `gunicorn` + `uvicorn` workers? → **Decisión tentativa**: `uvicorn` solo en dev; `gunicorn` + `uvicorn` en producción (configurado más adelante).
