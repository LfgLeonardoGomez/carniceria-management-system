# Tasks: C-15 Gastos

## Backend

- [x] 1.1 Write failing tests (test_gasto_integration.py) — RED
- [x] 1.2 Implement gasto/models.py — add Gasto table + keep CategoriaGasto
- [x] 1.3 Create Alembic migration 000000000013_add_gasto_table.py
- [x] 1.4 Implement gasto/schemas.py — GastoCreate, GastoUpdate, GastoRead, GastoListResponse
- [x] 1.5 Implement gasto/service.py — CRUD + _check_alerta_gasto_elevado stub
- [x] 1.6 Implement gasto/router.py — 5 endpoints with RBAC guards
- [x] 1.7 main.py already registers gasto_router at /gasto (pre-existing, no change needed)
- [x] 1.8 All 25 tests GREEN (25/25 passed)

## Frontend

- [x] 2.1 frontend/src/shared/types/gasto.ts — Gasto, GastoCreate, GastoUpdate types
- [x] 2.2 frontend/src/features/gastos/api.ts — fetchGastos, createGasto, updateGasto, deleteGasto
- [x] 2.3 frontend/src/features/gastos/GastosGrid.tsx — table with categoria/date filters
- [x] 2.4 frontend/src/features/gastos/GastoForm.tsx — form for create/edit
- [x] 2.5 frontend/src/stores/gastoStore.ts — Zustand store
- [x] 2.6 frontend/src/pages/GastosPage.tsx — page component

## Not in scope (deferred)

- [ ] Alert engine implementation (IN-04) — deferred as its own future change
- [x] Route registration in App.tsx — done 2026-06-21 (router already set up; /gastos wired with PrivateRoute)
