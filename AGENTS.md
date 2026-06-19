# BASILE — Instrucciones para Agentes

> **Proyecto**: BASILE — SaaS multiempresa para gestión integral de carnicerías.
> **Reglas globales**: El proyecto hereda `~/.claude/CLAUDE.md` (orquestador OPSX, governance, TDD, engram, conventional commits). Acá viven solo las reglas **específicas de BASILE** + las universales que el global no cubre.

---

## Stack Tecnológico

| Capa | Tecnología | Versión mínima | Nota |
|------|-----------|----------------|------|
| Frontend | React (SPA) | 18+ | TypeScript estricto, Zustand para state |
| Backend | FastAPI (Python) | 0.100+ | Async/await, Pydantic, inyección de dependencias |
| Base de datos | PostgreSQL | 14+ | RLS activo, transacciones ACID obligatorias |
| ORM | SQLAlchemy 2.0 / SQLModel | 2.0+ | Modelos declarativos, migraciones con Alembic |
| Auth | JWT (access + refresh) | — | Refresh token en httponly cookie; tenant en subclaim |
| Infra | Docker + Docker Compose | — | Local dev; cloud a definir |
| Testing | pytest + Vitest + Playwright | — | TDD obligatorio; testcontainers para DB real |

---

## Base de Conocimiento

| Archivo | Qué contiene |
|---------|-------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito, actores, alcance v1.0, métricas |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, arquitectura, integraciones, API REST |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Actores, matriz RBAC, rutas públicas |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, relaciones, constraints, seed data |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | 37 reglas codificadas por dominio (RN-XX-NN) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | 21 historias de usuario en 13 épicas |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | 6 flujos e2e con diagramas ASCII |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura de directorios, seguridad |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | 5 decisiones + 8 supuestos con riesgos |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | 10 inconsistencias + 12 preguntas abiertas |

**Leer antes de codear**: `10_preguntas_abiertas.md` — resolver las de prioridad **Alta** antes de Sprint 0.

---

## Skills Disponibles

| Skill | Rol | Cuándo se carga |
|-------|-----|-----------------|
| `fastapi` | Backend Core | Escribir/refactorizar endpoints, Pydantic models, dependencias |
| `supabase-postgres-best-practices` | Backend Core | Diseñar schema, queries, índices, RLS |
| `saas-multi-tenant` | Backend Core | Aislamiento de tenant, row-level security, data leakage prevention |
| `vercel-react-best-practices` | Frontend | Escribir/refactorizar componentes React, performance |
| `frontend-design` | Frontend | UI/UX, estilos, animaciones, diseño visual |
| `webapp-testing` | QA / Frontend | Testing E2E con Playwright, verificar UI |
| `typescript-e2e-testing` | QA / Frontend | Tests E2E e integración con TypeScript |
| `devops-engineer` | DevOps | CI/CD, Docker, deploy, infraestructura |
| `retail-expert` | Domain Expert | Decisions de negocio retail, POS, inventario, cuentas corrientes |

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo).

---

## Roadmap de Changes

20 changes organizados en 7 fases. Ver `CHANGES.md` completo para el árbol de dependencias y parallelism gates.

**Camino crítico**: C-01 → C-02 → C-04 → C-05 → C-08 → C-09 → C-10 → C-12 → C-13 → C-16 → C-17 → C-20

**Primer change**: `C-01-foundation-setup` → `/opsx:propose C-01-foundation-setup`

---

## Reglas Duras (específicas del proyecto)

Reglas globales ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las hereda. Acá viven solo las reglas **específicas de BASILE** + las universales que el global no cubre.

### Backend FastAPI
- **NUNCA** bloquear el event loop en endpoints I/O-bound → usar `async/await` siempre
- **NUNCA** usar `dict` plano para request/response bodies → Pydantic `BaseModel` con `extra='forbid'`
- Inyectar `db: AsyncSession`, `current_user`, `tenant` como dependencias en cada router
- Organizar routers por dominio: `/ventas`, `/stock`, `/desposte`, `/caja`, etc.

### PostgreSQL + Multi-tenant
- **NUNCA** omitir `empresa_id` en queries que mutan o leen datos de negocio → aislamiento estricto
- Activar RLS en TODAS las tablas de negocio como capa de seguridad adicional
- Usar transacciones ACID obligatorias para: ventas, caja (apertura/cierre), stock (ajustes), desposte
- Índices obligatorios en: `empresa_id`, `fecha`, `cliente_id`, `producto_id`, `estado`

### Frontend React/SPA
- **NUNCA** usar `any` → TypeScript `strict: true`; usar `unknown` + type narrowing
- Componentes funcionales + hooks exclusivamente; sin clases
- Zustand para state global; React Query / SWR para server state

### Seguridad
- JWT access token corto (15 min) + refresh token largo (7 días) en **httponly cookie**
- Validar `tenant_id` (desde subclaim del JWT o header `X-Empresa-Id`) en **cada request autenticado**
- Input validation en frontend **Y** backend (zero trust)

### Testing
- TDD obligatorio: test escrito **antes** del código productivo para toda lógica de negocio
- Backend: `pytest` + `pytest-asyncio` + `testcontainers` (PostgreSQL real, nunca SQLite en tests de integración)
- Frontend: `Vitest` + React Testing Library; `Playwright` solo para flujos E2E críticos (venta completa end-to-end)

### Datos y Negocio
- **NUNCA** usar `float` para dinero → `Decimal` en backend; frontend usa librería de precisión decimal
- Stock en kilos con precisión de **3 decimales** (0.001 kg)
- Fechas: UTC en DB, local en UI (timezone configurable por empresa en `config`)

---

## Flujo de Trabajo

```
knowledge-base/  →  CHANGES.md  →  /opsx:propose <change>  →  /opsx:apply  →  /opsx:archive
     ↑                                                                  ↓
     └───────────────────────── Leer KB antes de codear ←────────────────┘
```

1. **Antes de proponer**: leer `knowledge-base/` y `CHANGES.md`
2. **Proponer**: `/opsx:propose C-NN-nombre` genera proposal, design y tasks
3. **Aplicar**: `/opsx:apply C-NN-nombre` implementa tasks con TDD
4. **Archivar**: `/opsx:archive C-NN-nombre` sincroniza specs y cierra

---

## Model Assignments (subagentes)

| Fase | Modelo | Motivo |
|------|--------|--------|
| orchestrator | kimi-k2.6 | Coordinación y decisiones (actual) |
| explore | sonnet | Exploración de código, thinking partner |
| propose | kimi-k2.6 | Decisiones arquitectónicas |
| apply | deepseek-v4-flash | Implementación y coding |
| archive | deepseek-v4-flash | Operaciones de archivo y sync |
| default | sonnet | Delegación general |

> El orquestador (kimi-k2.6) lee esta tabla al inicio de sesión y pasa el `model` correspondiente en cada llamada al Agent tool.

### ⚠️ Regla explícita del orquestador
En **CADA llamada al Agent tool**, el orquestador DEBE incluir el parámetro `model` mapeado desde esta tabla. Omitir el parámetro `model` es un error crítico que infla costos innecesariamente.

**Aplicar (`/opsx:apply`)** → `model: "deepseek-v4-flash"`  
**Archivar (`/opsx:archive`)** → `model: "deepseek-v4-flash"`  
**Proponer (`/opsx:propose`)** → `model: "kimi-k2.6"`  
**Explorar (`/opsx:explore`)** → `model: "sonnet"`

Si el modelo asignado no está disponible, fallback a `sonnet` — NUNCA dejar que el sistema elija el default.

---

## Re-ejecutar fases individuales

- `/jr-orchestrator:kb` → regenerar KB desde docs/
- `/jr-orchestrator:rules` → regenerar este archivo
- `/jr-orchestrator:find-skill` → buscar/instalar nuevas skills
- `/jr-orchestrator:registry` → reconstruir `.atl/skill-registry.md`
