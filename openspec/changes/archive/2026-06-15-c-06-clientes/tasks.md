## 1. Database & Migration

- [x] 1.1 Create Alembic migration for `cliente` table (`id`, `empresa_id`, `nombre`, `apellido`, `razon_social`, `cuit`, `telefono`, `email`, `direccion`, `tipo_cliente`, `limite_cuenta_corriente`, `saldo_actual`, `activo`, `created_at`, `updated_at`)
- [x] 1.2 Add unique constraint `(empresa_id, cuit)` where `cuit IS NOT NULL`
- [x] 1.3 Add index on `(empresa_id, tipo_cliente)` and `(empresa_id, nombre)` for list filtering
- [x] 1.4 Add index on `(cliente_id, fecha)` on `venta` table for historial performance (if venta table exists; otherwise mark as deferred)
- [x] 1.5 Create RLS policy on `cliente` table: `USING (empresa_id = current_setting('app.current_tenant')::uuid)`
- [x] 1.6 Run migration and verify schema in dev/test databases

## 2. Backend — Domain Model & Schemas

- [x] 2.1 Create `Cliente` SQLModel in `backend/src/modules/cliente/models.py` with `Decimal` fields for money and `tipo_cliente` enum
- [x] 2.2 Create Pydantic request schemas: `ClienteCreate`, `ClienteUpdate` with `extra='forbid'`
- [x] 2.3 Create Pydantic response schema: `ClienteResponse` with `saldo_actual` included
- [x] 2.4 Add CUIT validation regex/normalization in `ClienteCreate`/`ClienteUpdate`
- [x] 2.5 Add `tipo_cliente` enum validation (publico_general, mayorista, especial)

## 3. Backend — Service & CRUD

- [x] 3.1 Implement `ClienteService` with `create`, `update`, `soft_delete`, `get_by_id`, `list`, `search` methods
- [x] 3.2 Ensure all service methods filter by `empresa_id` from authenticated user
- [x] 3.3 Implement `get_historial` method that queries `venta` by `cliente_id` with pagination and tenant filter
- [ ] 3.4 Add audit logging for create/update/delete operations (reuse C-04 audit infra if available)

## 4. Backend — Router & Dependencies

- [x] 4.1 Create `cliente_router` in `backend/src/modules/cliente/router.py` with routes:
  - `POST /cliente` (create)
  - `GET /cliente` (list with filters `tipo_cliente`, `q`, `limit`, `offset`)
  - `GET /cliente/{id}` (detail)
  - `PUT /cliente/{id}` (update)
  - `DELETE /cliente/{id}` (soft delete)
  - `GET /cliente/{id}/historial` (purchase history)
- [x] 4.2 Inject dependencies: `db: AsyncSession`, `current_user`, `tenant` (from C-03/C-04 patterns)
- [x] 4.3 Apply RBAC guards per role: Administrador = CRUD, Encargado = CRU, Cajero = CRU, Vendedor = 403
- [x] 4.4 Wire router into main FastAPI app

## 5. Frontend — State & API

- [x] 5.1 Create Zustand store `useClientesStore` for filter state (`tipo_cliente`, `searchQuery`, `pagination`)
- [x] 5.2 Create React Query hooks: `useClientes`, `useCliente`, `useClienteHistorial`, `useCreateCliente`, `useUpdateCliente`, `useDeleteCliente`
- [x] 5.3 Define TypeScript interfaces: `Cliente`, `ClienteCreate`, `ClienteUpdate`, `VentaResumen` (for historial)
- [x] 5.4 Create API client functions in `frontend/src/features/clientes/api.ts`

## 6. Frontend — UI Components

- [x] 6.1 Build `ClientesGrid` page with table, search bar, and `tipo_cliente` filter dropdown
- [x] 6.2 Build `ClienteDetail` page with profile card, purchase history list, and saldo display
- [x] 6.3 Build `ClienteForm` modal for create/edit with validation
- [x] 6.4 Add soft-delete confirmation dialog
- [x] 6.5 Add route entries in React Router (`/clientes`, `/clientes/:id`)

## 7. Tests — Backend

- [x] 7.1 Write `test_cliente_service.py`: create, read, update, soft delete with tenant isolation
- [x] 7.2 Write `test_cliente_integration.py`: historial endpoint returns correct sales, pagination, tenant isolation
- [x] 7.3 Write `test_cliente_service.py`: `saldo_actual` is included in read response and defaults to 0.00
- [x] 7.4 Write `test_cliente_integration.py`: role-based access enforcement for each endpoint
- [x] 7.5 Write `test_cliente_service.py` + `test_cliente_integration.py`: search by name, apellido, razon_social, cuit
- [x] 7.6 Run all backend tests with pytest + testcontainers (PostgreSQL real) — **45 passed**

## 8. Tests — Frontend

- [x] 8.1 Write Vitest unit tests for `ClienteForm` validation and submission
- [x] 8.2 Write Vitest unit tests for `ClientesGrid` filtering logic
- [ ] 8.3 Write Playwright E2E test: full client CRUD flow from grid to detail
- [ ] 8.4 Write Playwright E2E test: search and filter by tipo_cliente

## 9. Integration & Verification

- [ ] 9.1 Run `openspec verify` against `c-06-clientes` to ensure all specs are covered by implementation
- [ ] 9.2 Verify `/clientes` endpoints in Swagger UI with tenant header/cookie
- [ ] 9.3 Verify frontend client grid and detail views render correctly
- [ ] 9.4 Verify RLS policy blocks cross-tenant access at DB level
- [ ] 9.5 Update `CHANGES.md` status for C-06 to "implemented"
