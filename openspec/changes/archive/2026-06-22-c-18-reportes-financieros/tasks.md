# Tasks: C-18 — Reportes financieros

> **TDD is mandatory.** For every backend behavior write the failing pytest first
> (real PostgreSQL via testcontainers — never SQLite for integration), make it
> pass, then triangulate with a second case. Frontend behavior: Vitest + RTL test
> first. Money is `Decimal` (never float). Every query is scoped to `empresa_id`.
> **Coexistence rule (binding):** only ADD symbols to `reporte/schemas.py`,
> `service.py`, `router.py` — never edit C-17's `/reportes/ventas` handlers,
> schemas, or `listar_ventas_reporte`.

## 1. Backend — schemas (Decision 6)

- [x] 1.1 RED: test that `GroupBy` accepts `dia|semana|mes|anio` and rejects other values; that `FinancieroPeriodoRow` forbids extra fields (`extra='forbid'`) and allows `costos|utilidad_bruta|utilidad_neta` to be null while `ventas|gastos` are required Decimals.
- [x] 1.2 GREEN: add `GroupBy`, `FinancieroPeriodoRow`, `ReporteFinancieroResponse` to `backend/src/modules/reporte/schemas.py` (append only; do not touch C-17 schemas). Decimal-safe serialization, `model_config = {"extra": "forbid"}`.
- [x] 1.3 TRIANGULATE: assert money fields serialize Decimal-safe (string, no float drift) and that an unknown field on the row raises a validation error.

## 2. Backend — period bucketing helper (Decision 2)

- [x] 2.1 RED: write tests for a pure `periodo_key(fecha, group_by)` helper covering each group_by — `dia` → `YYYY-MM-DD`, `semana` → ISO `YYYY-Www`, `mes` → `YYYY-MM`, `anio` → `YYYY` — with at least one edge case (year boundary for `semana`/`anio`, e.g. 2025-12-31 vs 2026-01-01).
- [x] 2.2 GREEN: implement `periodo_key` in `reporte/service.py`, normalizing `datetime` (UTC) and `date` inputs to the same UTC calendar before keying so ventas and gastos buckets align.
- [x] 2.3 TRIANGULATE: add a second case per group_by with different inputs; confirm a venta `datetime` and a gasto `date` in the same period produce the identical key.

## 3. Backend — financial aggregation service (Decisions 3, 4)

- [x] 3.1 RED (formulas): test `reporte_financiero` for a single bucket with known ventas/costos/gastos — assert `utilidad_bruta = ventas − costos` and `utilidad_neta = utilidad_bruta − gastos` (e.g. 1000/600/150 → bruta 400, neta 250).
- [x] 3.2 RED (cost contract / NULL never zero): test that a bucket containing any `DetalleVenta.costo_unitario IS NULL` line returns `costos = None`, `utilidad_bruta = None`, `utilidad_neta = None`, while `ventas` and `gastos` stay present. Reuse / mirror the exact `calcular_ganancia` contract (do not treat NULL as 0).
- [x] 3.3 RED (snapshot immutability): test that changing a product's current cost after a sale does NOT change the reported `costos` for that sale's period (uses the stored snapshot, not current product cost).
- [x] 3.4 GREEN: implement `reporte_financiero(db, empresa_id, group_by, fecha_desde, fecha_hasta)` — three tenant-scoped queries (cobrada ventas + their `DetalleVenta` via `selectinload`; gastos), bucket by `periodo_key`, compute the five indicators per bucket reusing the `calcular_ganancia` cost logic, merge on period key, return rows ordered chronologically.
- [x] 3.5 RED (only cobrada): test that non-`cobrada` sales (en_curso/suspendida/anulada) are excluded from `ventas` and `costos`.
- [x] 3.6 RED (gastos affect net only): test two otherwise-identical periods where only one has gastos → same `utilidad_bruta`, lower `utilidad_neta` for the one with gastos.
- [x] 3.7 TRIANGULATE: test multi-bucket aggregation (e.g. `group_by=mes` over 3 months with data in two) and an empty range → empty `rows` list (not an error).

## 4. Backend — multi-tenant isolation (spec: Multi-tenant isolation)

- [x] 4.1 RED: seed empresa A and empresa B with ventas and gastos in the same period; assert empresa A's report contains ONLY A's ventas/costos/gastos and none of B's. (At least 3 tenants in the broader fixture per multi-tenant best practice.)
- [x] 4.2 GREEN: confirm every query in `reporte_financiero` filters on `empresa_id` first; no code change if 3.4 already correct, otherwise fix.
- [x] 4.3 TRIANGULATE: swap the requesting empresa and assert the indicators flip to that tenant's data only.

## 5. Backend — router + access control (Decisions 1, 6)

- [x] 5.1 RED: integration test `GET /reportes/financieros?group_by=mes` returns 200 with the response schema for an administrator (holding `reportes:read`); a user without `reportes:read` gets 403.
- [x] 5.2 RED: `group_by=trimestre` (invalid) returns 422 and runs no query; missing `group_by` defaults to `mes`.
- [x] 5.3 GREEN: add the `GET /reportes/financieros` route to `reporte/router.py` — inject `db`, `current_user`; derive `empresa_id = current_user.empresa_id`; guard with `Depends(require_role("reportes:read"))`; call `service.reporte_financiero`. Append only; do not edit C-17 routes.
- [x] 5.4 TRIANGULATE: assert the date-range filter (`fecha_desde`/`fecha_hasta`) narrows results and that omitting it returns all periods for the empresa.
- [x] 5.5 Verify the route is reachable via the already-mounted `reporte_router` (prefix `/reportes`) — no new `include_router` needed; confirm no migration was added.

## 6. Backend — coexistence guard with C-17 (Decision 1)

- [x] 6.1 Confirm (and assert in a focused test or review note) that `listar_reporte_ventas`, `exportar_reporte_ventas`, `VentaReporteRow`, `ReporteVentasResponse`, and `listar_ventas_reporte` are unchanged by this change — C-18 is append-only.

## 7. Frontend — data hook (Decision 7)

- [x] 7.1 RED: Vitest test for `useReporteFinanciero` — fetches `/reportes/financieros` with `group_by` + date-range params, returns typed rows; null indicators stay null (not coerced to 0). TypeScript strict, no `any`.
- [x] 7.2 GREEN: implement `frontend/src/features/reportes/useReporteFinanciero.ts` with React Query; typed against the backend response.

## 8. Frontend — view (charts + table) (spec: Financial reports frontend view)

- [x] 8.1 RED: RTL test for `FinancieroTable` — renders one row per period with the five indicators; a period with null `costos` renders a distinct "no disponible" marker, NOT `0`.
- [x] 8.2 GREEN: implement `FinancieroTable.tsx` and `FinancieroFilters.tsx` (group_by selector + date range).
- [x] 8.3 RED: RTL test for `FinancieroChart` — renders a comparative chart for the selected grouping; reuse whatever charting library C-16 dashboard already uses (verify; do not add a new dependency if one exists).
- [x] 8.4 GREEN: implement `FinancieroChart.tsx` and `ReportesFinancierosPage.tsx`; wire filters → hook → chart + table.
- [x] 8.5 GREEN: add the `/reportes/financieros` route in `App.tsx`, visible only to authorized roles (administrador). 403 from the API shows a "No autorizado" message.
- [x] 8.6 TRIANGULATE: test that changing `group_by` (mes → dia) refetches and re-renders chart + table with the new buckets; format money with a precision-decimal lib (never JS `number` arithmetic).

## 9. Wrap-up

- [x] 9.1 Run the full backend suite (pytest + testcontainers) and frontend suite (Vitest) — all green.
- [x] 9.2 Confirm no Alembic migration and no new SQLModel table were introduced (read-only change).
- [x] 9.3 Self-review against the spec scenarios (RN-REP-04 groupings, RN-REP-05 indicators, NULL-never-zero, multi-tenant isolation) and the C-17 coexistence rule.
