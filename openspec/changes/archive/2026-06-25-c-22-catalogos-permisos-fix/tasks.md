## 1. Backend — Seed de categorías por empresa

- [x] 1.1 Modificar `backend/src/database/seeds/run.py`: importar `Empresa`, query `session.query(Empresa).all()` después de `seed_admin_user`.
- [x] 1.2 Iterar sobre cada empresa y llamar `seed_categorias_producto(session, empresa_id=empresa.id)`.
- [x] 1.3 Confirmar que `seed_categorias_producto` sigue siendo idempotente (re-ejecutable sin duplicar).
- [x] 1.4 Verificar en DB: `SELECT nombre, empresa_id FROM categoria_producto WHERE empresa_id IS NOT NULL;` devuelve 5 filas para "Carnicería Don Juan".

## 2. Backend — Seed de permisos RBAC

- [x] 2.1 Crear `backend/src/database/seeds/permisos.py` con función `seed_permisos(session)` que itera los 6 roles y popula `rol.permisos` desde `PERMISSION_MATRIX`.
- [x] 2.2 Formato JSON: `{"recurso": ["operacion", ...]}` (ej. `{"productos": ["read", "create", "update", "delete"]}`).
- [x] 2.3 Idempotente: si el rol ya tiene permisos, los sobreescribe con el valor actual de la matriz.
- [x] 2.4 Agregar rol `desposte` (UUID determinístico via `uuid.uuid5`) a `roles.py` (`ROLES` list).
- [x] 2.5 Modificar `backend/src/common/rbac.py`: agregar `desposte` a `PERMISSION_MATRIX` y `normalize_rol` mapping.
- [x] 2.6 Modificar `run.py` para llamar `seed_permisos(session)` después de `seed_roles`.
- [x] 2.7 Verificar en DB: `SELECT nombre, permisos FROM rol WHERE nombre='admin';` devuelve JSON con `productos`, `clientes`, `desposte`, etc.

## 3. Backend — Endpoint `GET /desposte/tipos`

- [x] 3.1 Agregar schema `TipoCorteRead` a `backend/src/modules/desposte/schemas.py` con campos `id: uuid.UUID` y `nombre: str`.
- [x] 3.2 Crear endpoint en `backend/src/modules/desposte/router.py`: `@router.get("/tipos", response_model=list[TipoCorteRead], dependencies=[Depends(require_role("desposte:read"))])`.
- [x] 3.3 Implementación: `select(TipoCorte).order_by(TipoCorte.nombre)`.
- [x] 3.4 Ruta está antes de `/{desposte_id}` para evitar shadowing.
- [x] 3.5 Verificar con curl: `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/desposte/tipos` devuelve 12 items.

## 4. Backend — Fix bug de strings de permiso en router de desposte

- [x] 4.1 Reemplazar 5 ocurrencias de `require_role("despostes:*")` por `require_role("desposte:*")` en `backend/src/modules/desposte/router.py`.
- [x] 4.2 Verificar que `GET /desposte` ya no devuelve 403 para admin.

## 5. Frontend — Sidebar copy

- [x] 5.1 Cambiar label "POS" → "Venta" en `frontend/src/components/layout/menuConfig.ts` (path `/pos` queda igual).
- [x] 5.2 Verificar que `menuConfig.test.ts` sigue pasando (solo chequea path, no label).

## 6. Tests y verificación

- [x] 6.1 Agregar test `test_seed_permisos_pobla_matriz` en `backend/tests/test_seed_data.py` que valide que `seed_permisos` setea el JSON.
- [x] 6.2 Agregar test de integración `test_desposte_tipos_endpoint` que valide `GET /desposte/tipos` con token de admin.
- [x] 6.3 Re-correr seeds: `docker-compose exec backend python src/database/seeds/run.py` — debe ser idempotente.
- [x] 6.4 Suite completa: `pytest` y `npm run test` (o `vitest`).

## 7. Documentación OPSX

- [x] 7.1 Crear `openspec/changes/c-22-catalogos-permisos-fix/proposal.md` (este change).
- [x] 7.2 Crear `openspec/changes/c-22-catalogos-permisos-fix/tasks.md` (este archivo).
- [x] 7.3 Crear delta specs para `seed-data`, `rbac-middleware`, `frontend-layout` y `backend-catalogs` (desposte/tipos endpoint).
