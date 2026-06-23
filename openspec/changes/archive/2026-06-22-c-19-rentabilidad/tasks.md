# Tasks: c-19-rentabilidad

> TDD is MANDATORY. For every behavior: write the failing test first (RED),
> minimum code to pass (GREEN), triangulate with a second case, then refactor.
> Backend: pytest + pytest-asyncio; integration tests use real PostgreSQL via
> testcontainers (never SQLite). Frontend: Vitest + React Testing Library.
> Money is always Decimal; NULL margin is NEVER zero.

## 1. Backend module scaffolding

- [x] 1.1 Create `backend/src/modules/rentabilidad/` package
  (`__init__.py`, `router.py`, `service.py`, `schemas.py`), mirroring the
  `reporte` module layout.
- [x] 1.2 Register `rentabilidad_router` in `backend/src/main.py` under prefix
  `/rentabilidad`, tag `rentabilidad`, with `dependencies=auth_dep`.
- [x] 1.3 Add an import smoke test (extend `test_backend_imports.py` or add a
  rentabilidad test) asserting the module and router import cleanly.

## 2. Schemas (Decision 6)

- [x] 2.1 RED: test that `ProductoRentabilidadRow` and
  `CorteRentabilidadRow` reject unknown fields (`extra='forbid'`) and accept
  `Optional[Decimal]` for `ganancia` / `margen_porcentaje` /
  `precio_venta_promedio`.
- [x] 2.2 GREEN: implement `ProductoRentabilidadRow`
  (`producto_id`, `nombre`, `ventas`, `ganancia?`, `margen_porcentaje?`),
  `CorteRentabilidadRow` (`tipo_corte`, `producto_id`, `nombre_producto`,
  `costo_por_kilo`, `precio_venta_promedio?`, `margen_por_kilo?`,
  `margen_porcentaje?`), and their response wrappers
  (`RentabilidadProductosResponse`, `RentabilidadCortesResponse`), with the
  `Orden = Literal["mayor", "menor"]` type.

## 3. Pure aggregation helpers (Decision 2, 3, 5)

- [x] 3.1 RED: unit-test `_ranking_productos(detalles)` for the happy path —
  `ganancia = Σ(importe) − Σ(kilos × costo_unitario)`,
  `margen_porcentaje = ganancia / ventas × 100` (e.g. 1000/600 → 400 / 40.00).
- [x] 3.2 GREEN: implement `_ranking_productos` aggregating per `producto_id`.
- [x] 3.3 TRIANGULATE: a product with ANY line `costo_unitario IS NULL` →
  `ganancia` and `margen_porcentaje` are `None` (never zero); a product with
  `ventas == 0` → margin `None`.
- [x] 3.4 RED+GREEN: ordering — `orden=mayor` sorts margin descending,
  `orden=menor` ascending; null-margin products always ordered LAST in both
  directions (deterministic); `top=N` limits the head.
- [x] 3.5 RED: unit-test `_margen_cortes(cortes, detalles)` — per linked product
  average price `Σ(importe)/Σ(kilos)`, `margen_por_kilo = precio − costo`,
  `margen_porcentaje = margen / precio × 100` (e.g. costo 800, precio 1000 →
  200 / 20.00).
- [x] 3.6 GREEN: implement `_margen_cortes`.
- [x] 3.7 TRIANGULATE: cut with `producto_id IS NULL` is EXCLUDED from the
  result; cut whose linked product has no sales in range →
  `precio_venta_promedio` and `margen_porcentaje` are `None` (never zero price).

## 4. Service query functions (Decision 7)

- [x] 4.1 Implement async `ranking_productos(db, empresa_id, fecha_desde,
  fecha_hasta, orden, top)` — tenant-scoped query of cobrada ventas + detalles
  over the UTC calendar-day range (mirror `reporte_financiero` bounds), then call
  `_ranking_productos`.
- [x] 4.2 Implement async `margen_cortes(db, empresa_id, fecha_desde,
  fecha_hasta)` — tenant-scoped query of `CorteDesposte` (with `producto_id`) and
  the cobrada sale lines for the linked products over the range, then call
  `_margen_cortes`.

## 5. Endpoints

- [x] 5.1 `GET /rentabilidad/productos` — query params `fecha_desde?`,
  `fecha_hasta?`, `orden` (default `mayor`), `top?` (positive int); guarded by
  `require_role("reportes:read")`; `empresa_id` from `current_user`.
- [x] 5.2 `GET /rentabilidad/cortes` — query params `fecha_desde?`,
  `fecha_hasta?`; guarded by `require_role("reportes:read")`; `empresa_id` from
  `current_user`.

## 6. Backend integration tests (real PostgreSQL via testcontainers)

- [x] 6.1 Products ranking happy path returns rows with correct ganancia/margen
  and `orden` ordering.
- [x] 6.2 NULL `costo_unitario` → product margin null (not zero) and ordered last.
- [x] 6.3 Multi-tenant isolation: empresa A request never returns empresa B
  products or cuts.
- [x] 6.4 Access control: `reportes:read` role → 200; cajero (no permission) →
  403, for both endpoints.
- [x] 6.5 Cortes: matched cut returns margin; `producto_id IS NULL` cut excluded;
  linked product with no sales → null `precio_venta_promedio`.
- [x] 6.6 Date-range filter narrows results; no range aggregates all cobrada
  sales for the empresa.

## 7. Frontend — data layer

- [x] 7.1 Add TS types for the two responses in
  `frontend/src/features/rentabilidad/` (strict, no `any`; Decimal-safe string
  parsing consistent with the reportes feature).
- [x] 7.2 RED+GREEN: React Query hooks `useRentabilidadProductos(filters)` and
  `useRentabilidadCortes(filters)` (mirror `useReporteFinanciero`), with tests.

## 8. Frontend — view

- [x] 8.1 `RentabilidadProductosTable` + comparison chart, with
  most/least toggle and Top-N control; null margin rendered as a distinct
  "no disponible" marker (with test).
- [x] 8.2 `RentabilidadCortesTable` + comparison chart; null margin rendered
  distinctly (with test).
- [x] 8.3 `RentabilidadFilters` (date range) shared by both tabs (with test).
- [x] 8.4 `RentabilidadPage` under `frontend/src/pages/` composing the tabs;
  general-profitability tab reuses the existing financial report
  (`useReporteFinanciero`) for CA-4 — no new general endpoint.
- [x] 8.5 Route + nav entry gated to authorized roles (administrador/encargado).

## 9. Verification

- [x] 9.1 Run the full backend test suite — all rentabilidad tests green, no
  regression in `reporte`/`venta`/`desposte` suites.
- [x] 9.2 Run the frontend test suite — all rentabilidad tests green.
- [x] 9.3 Confirm no `/rentabilidad/general` route exists and CA-4 is served by
  `GET /reportes/financieros`.
