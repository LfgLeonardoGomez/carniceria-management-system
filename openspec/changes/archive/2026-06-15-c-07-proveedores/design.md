## Context

El proyecto BASILE es un SaaS multiempresa para gestión de carnicerías. El change `C-03 empresa-config` ya está completado y la tabla `empresa` existe. El módulo de proveedores es un catálogo core que habilita el registro de compras de media res en `C-08`. Actualmente, los directorios `backend/src/modules/proveedor/` y `frontend/src/features/proveedores/` existen como placeholders vacíos.

## Goals / Non-Goals

**Goals:**
- Proporcionar un CRUD completo de proveedores con aislamiento estricto multi-tenant (`empresa_id`).
- Implementar búsqueda por nombre con índice optimizado.
- Implementar endpoint de historial de compras inmutable (placeholder para C-08).
- Construir el frontend de grid, formulario y ficha detalle.
- Cubrir con tests de backend (pytest + testcontainers) y frontend (Vitest).
- Aplicar las reglas duras del proyecto: nunca `float` para dinero, nunca `dict` plano para bodies, `async/await` en endpoints I/O-bound, Pydantic `extra='forbid'`.

**Non-Goals:**
- No se implementa la tabla `Compra` en este change (va en C-08); el historial devuelve `[]` si no hay datos.
- No se implementa importación masiva de proveedores (no requerido en v1.0).
- No se agrega soft-delete con `activo` (el modelo actual no lo tiene; si se necesita, se agrega en iteración futura).

## Decisions

### 1. SQLModel para el modelo de Proveedor
**Rationale**: El proyecto usa SQLModel/SQLAlchemy 2.0 como ORM. `Proveedor` es un modelo declarativo con `empresa_id` como FK a `Empresa`. Esto mantiene consistencia con C-03 y C-04.

### 2. Baja lógica vía `activo` flag
**Rationale**: Aunque la KB no explicita `activo` en `Proveedor`, RN-GLOBAL-02 prohíbe eliminación física de datos. Se agrega campo `activo` (boolean, default `true`) para baja lógica. Esto evita romper referencias futuras en `Compra`.

### 3. Endpoint de historial como LEFT JOIN a `Compra` con safe-fallback
**Rationale**: `Compra` no existe todavía. El endpoint `GET /proveedores/{id}/historial` hará un LEFT JOIN a `compra` filtrando por `proveedor_id` y `empresa_id`. Si la tabla no existe, el endpoint devuelve `[]` sin fallar. Esto garantiza que la interfaz de frontend no cambie cuando C-08 se aplique.

### 4. Índice compuesto `(empresa_id, nombre)` + `(empresa_id, cuit)`
**Rationale**: La búsqueda principal es por nombre. El índice acelera filtros y sorting. `cuit` es opcional pero si se usa, debe ser único por empresa. Se agrega índice único parcial `(empresa_id, cuit)` donde `cuit IS NOT NULL`.

### 5. Frontend: React Query (SWR) para server state, Zustand para UI state
**Rationale**: Consistente con la arquitectura del proyecto. El grid de proveedores usa React Query para cachear listados; el formulario de edición usa mutaciones optimistas.

### 6. RBAC en middleware + route guards
**Rationale**: Según la matriz RBAC, solo Administrador y Encargado tienen CRUD en proveedores. El router de backend valida el rol en cada endpoint. El frontend oculta rutas según el rol del usuario autenticado.

## Risks / Trade-offs

- **[Risk]** `Compra` no existe todavía → el historial devuelve vacío.
  - **Mitigation**: El endpoint está diseñado para funcionar con LEFT JOIN; cuando C-08 se aplique, solo se necesita agregar la relación y el join funciona sin cambiar la API.
- **[Risk]** `cuit` puede ser NULL para muchos proveedores informales.
  - **Mitigation**: Se permite NULL en la DB y se valida formato (11 dígitos) solo cuando se proporciona.
- **[Risk]** El frontend de proveedores es similar al de clientes (C-06) y podría duplicar código.
  - **Mitigation**: Se extraerán componentes genéricos de formulario y grid si la estructura es idéntica, pero no se bloquea este change por DRY — la refactorización se puede hacer en C-06 o post-merge.

## Migration Plan

1. **Database**: Alembic migration para crear tabla `proveedor` con índices y RLS policy.
2. **Backend**: Implementar modelos, schemas, service y router. Agregar tests.
3. **Frontend**: Implementar feature completo con rutas, componentes, hooks y servicios.
4. **Verify**: Correr tests backend (`pytest`) y frontend (`vitest`).
5. **Rollback**: Drop table `proveedor` si es necesario (perdida de datos aceptable en dev/staging; en producción se usa `activo = false` para baja lógica).

## Open Questions

- ¿Se necesita campo `observaciones` en `Proveedor`? (No está en la KB ni en US-008; se omite por ahora.)
- ¿Se necesita paginación en el grid de frontend? (Sí, estándar del proyecto; se implementa con `skip`/`limit` en backend.)
