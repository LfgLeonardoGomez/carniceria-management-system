# Design: C-18 — Reportes financieros

## Context

The `reporte` module already exists and is being extended by **C-17
(reportes-ventas, in progress)**, which adds `GET /reportes/ventas` and
`GET /reportes/ventas/exportar`. The router is already mounted in `main.py`:

```python
app.include_router(reporte_router, prefix="/reportes", tags=["reportes"], dependencies=auth_dep)
```

and both existing routes are guarded by `Depends(require_role("reportes:read"))`
(the `reportes:read` permission is already granted to the administrador role in
`backend/src/common/rbac.py`).

Dependencies (both DONE):
- **C-12 ventas-cobro** provides `Venta` (with `fecha: datetime` UTC, `total`,
  `estado`), `DetalleVenta` (with `cantidad_kilos`, immutable
  `costo_unitario: Optional[Decimal]` cost snapshot), and the pure helper
  `calcular_ganancia(lineas) -> Optional[Decimal]` in `venta/service.py`, whose
  cost contract is `Σ(cantidad_kilos × costo_unitario)` and which returns `None`
  if **any** line's `costo_unitario IS NULL`. Indexes exist on
  `(empresa_id, fecha)`.
- **C-15 gastos** provides `Gasto` with `empresa_id`, `fecha: date`,
  `importe: Decimal(2dp)`, and index `ix_gasto_empresa_id_fecha`.

C-18 adds the financial view US-018 (RN-REP-04, RN-REP-05): five indicators
(ventas, costos, gastos, utilidad bruta, utilidad neta) aggregated by
day/week/month/year.

## Goals / Non-Goals

**Goals:**
- `GET /reportes/financieros?group_by=<dia|semana|mes|anio>&fecha_desde&fecha_hasta`
  returning one bucket per period with the five indicators.
- Reuse the C-12 cost contract (no re-derivation of costs from current product cost).
- Strict multi-tenant isolation on every query (`empresa_id` from JWT).
- Coexist cleanly with C-17: same module/router, **separate route**, no edits to
  `/reportes/ventas`.
- Frontend financial view with comparative charts + table.

**Non-Goals:**
- Per-product / per-corte margin ranking → **C-19 (rentabilidad)**.
- Export (xlsx/csv/pdf) of the financial report.
- Materialized views, read models, scheduled reports, forecasting.
- Any new DB table, column, or migration (confirmed read-only — see Decision 5).

## Decisions

### Decision 1: Separate route in the shared module (coexistence with C-17)

**Chosen**: Add **one new route** `GET /reportes/financieros` to the existing
`reporte/router.py`. C-17's `/reportes/ventas` and `/reportes/ventas/exportar`
are left untouched. New schemas go in the same `reporte/schemas.py`; new service
logic in the same `reporte/service.py` as a new function `reporte_financiero(...)`.

**Rationale**: Both are reports under the same capability area, share the same
router prefix (`/reportes`), the same auth dependency, and the same
`reportes:read` guard. Reusing the mounted router avoids a second registration
and keeps the URL space coherent. Keeping the route **separate** (not a mode flag
on `/reportes/ventas`) means C-17 and C-18 can be implemented/merged in parallel
with zero shared-handler edits — they only append sibling definitions.

**Coexistence rule (binding for apply)**: C-18 MUST NOT modify the
`listar_reporte_ventas` / `exportar_reporte_ventas` handlers, the
`VentaReporteRow` / `ReporteVentasResponse` schemas, or `listar_ventas_reporte`.
It only ADDS new symbols. This avoids merge conflicts with the in-progress C-17.

**Alternatives considered**:
- *Mode parameter on `/reportes/ventas`* — rejected: overloads a stable contract
  and forces edits to C-17 handlers (merge risk, conflated responsibilities).
- *New `reporte_financiero` module* — rejected: would duplicate router
  registration and RBAC wiring for no benefit; the work is one read-only route.

### Decision 2: `group_by` handling — enum param + per-period truncation in Python

**Chosen**: `group_by: Literal["dia","semana","mes","anio"]` as a required-ish
query param (default `mes`). Invalid values are rejected by FastAPI/Pydantic with
**HTTP 422** before any query runs. Period bucketing is done by computing a
deterministic **period key** per source row in Python after loading the rows.

The period key is derived from the row's date (UTC):
- `dia` → `date` (YYYY-MM-DD)
- `semana` → ISO year-week (`(iso_year, iso_week)`), rendered as `YYYY-Www`
- `mes` → `(year, month)`, rendered as `YYYY-MM`
- `anio` → `year`, rendered as `YYYY`

**Rationale**: Doing bucketing in Python (rather than SQL `date_trunc`) lets the
sales side reuse the **exact** `calcular_ganancia` NULL-propagation contract per
bucket: we must group the `DetalleVenta` lines by period and decide
availability **per bucket** (if any line in a bucket lacks a cost snapshot, that
bucket's cost is null). A pure SQL `SUM(... )` cannot express "null if any line
null" without re-encoding the contract and risking divergence from C-12. Volumes
are bounded by the date filter and this is a reporting path, not OLTP.

**Note on `Venta.fecha` (datetime, UTC) vs `Gasto.fecha` (date)**: both are
normalized to a `date` (or ISO-week/month/year) on the same calendar in UTC
before keying, so a ventas bucket and a gastos bucket for the same period share
the same key and merge correctly.

**Alternatives considered**:
- *SQL `date_trunc` + `GROUP BY`* — faster, but cannot honor the per-bucket
  "null if any cost snapshot null" rule without re-implementing the cost contract
  in SQL. Deferred as a future optimization if profiling demands it.

### Decision 3: Cost & profit semantics — reuse the `calcular_ganancia` contract

**Chosen**: For each period bucket of cobrada sales:
- `ventas` = Σ `venta.total` of sales in the bucket (always available).
- `costos` = Σ over the bucket's `DetalleVenta` of `cantidad_kilos × costo_unitario`,
  **but null if any line in the bucket has `costo_unitario IS NULL`** — exactly
  the rule `calcular_ganancia` encodes. Reuse that helper's logic/contract rather
  than re-deriving it (import and apply `calcular_ganancia` per bucket, or apply
  its documented formula line-for-line so behavior is identical).
- `utilidad_bruta` = `ventas − costos`, **null when `costos` is null**.
- `utilidad_neta` = `utilidad_bruta − gastos`, **null when `utilidad_bruta` is null**.

**NULL is never zero** (binding): a missing cost snapshot makes `costos`,
`utilidad_bruta`, and `utilidad_neta` unavailable for that bucket. The schema
carries them as `Optional[Decimal]` and the response signals unavailability so
the frontend renders "no disponible", not `0.00`. `gastos` and `ventas` remain
available regardless.

**Rationale**: Treating an unknown cost as zero would silently overstate profit
and corrupt historical financials. C-12 already made the deliberate choice that
ganancia is `None` when any cost snapshot is missing; the financial report must
inherit that exactly.

### Decision 4: Query strategy — three tenant-scoped queries, merged in Python

**Chosen**: Per request:
1. Load cobrada `Venta` rows (with their `DetalleVenta` lines via `selectinload`)
   for `empresa_id` within the date range. Used for `ventas` and `costos`.
2. Load `Gasto` rows for `empresa_id` within the date range. Used for `gastos`.
3. Bucket each by period key, compute the five indicators per bucket, merge on
   the period key, and return buckets ordered chronologically.

All three queries filter on `empresa_id` first (leftmost index column) and the
date range, using the existing `(empresa_id, fecha)` indexes on both `venta` and
`gasto`. `estado = 'cobrada'` mirrors C-17's filter (only realized revenue counts).

**Rationale**: Sales and gastos live in different tables with no join key beyond
empresa+period; computing each side independently and merging on the period key
is the simplest correct approach and reuses the cost contract cleanly.

### Decision 5: No new model, no migration (read-only confirmed)

**Chosen**: C-18 introduces **no** SQLModel table, column, or Alembic migration.
It reads existing `venta`, `detalle_venta`, and `gasto`. `reporte/models.py`
stays a stub.

**Confirmation**: all five indicators are derivable from existing columns
(`venta.total`, `venta.estado`, `venta.fecha`, `detalle_venta.cantidad_kilos`,
`detalle_venta.costo_unitario`, `gasto.importe`, `gasto.fecha`). The indexes
needed (`(empresa_id, fecha)` on both tables) already exist. **No migration is
expected or created.**

### Decision 6: Schema shape — Decimal-safe, `extra='forbid'`, explicit nullability

```python
# reporte/schemas.py  (ADDED — alongside existing C-17 schemas)
GroupBy = Literal["dia", "semana", "mes", "anio"]

class FinancieroPeriodoRow(BaseModel):
    model_config = {"extra": "forbid"}
    periodo: str                              # e.g. "2026-06", "2026-W25", "2026"
    ventas: Decimal                           # 2dp, always present
    gastos: Decimal                           # 2dp, always present
    costos: Optional[Decimal] = None          # null if any cost snapshot missing
    utilidad_bruta: Optional[Decimal] = None  # null when costos is null
    utilidad_neta: Optional[Decimal] = None   # null when utilidad_bruta is null

class ReporteFinancieroResponse(BaseModel):
    model_config = {"extra": "forbid"}
    group_by: GroupBy
    rows: List[FinancieroPeriodoRow]
```

Monetary values serialize Decimal-safe (string), consistent with C-17 schemas.
The router handler injects `db: AsyncSession`, `current_user`, derives
`empresa_id = current_user.empresa_id`, and is guarded by
`Depends(require_role("reportes:read"))`.

### Decision 7: Frontend — charts + comparative table, React Query hook

**Chosen**: A new financial-reports page/feature under
`frontend/src/features/reportes/` (sibling to C-17's components — do not edit
C-17's files):
```
frontend/src/
├── pages/ReportesFinancierosPage.tsx        (NEW)
├── features/reportes/
│   ├── FinancieroFilters.tsx                 (NEW — group_by selector + date range)
│   ├── FinancieroChart.tsx                   (NEW — comparative chart)
│   ├── FinancieroTable.tsx                   (NEW — one row per period, 5 indicators)
│   └── useReporteFinanciero.ts               (NEW — React Query fetch hook)
└── App.tsx                                   (ADD /reportes/financieros route)
```
TypeScript strict (no `any`); functional components + hooks; React Query for
server state; a precision-decimal library for any client-side formatting (never
JS `number` arithmetic on money). Null indicators render as a distinct
"no disponible" marker. Charting library choice (e.g. Recharts) is finalized at
apply time; pick whatever the dashboard (C-16) already uses to stay consistent —
verify in apply and reuse it rather than adding a new dependency.

## Risks / Trade-offs

- **Per-bucket NULL propagation cost** → if a single old pre-snapshot sale lands
  in a wide bucket (e.g. `group_by=anio`), the whole year's `costos`/utilities go
  null. **Mitigation**: this is correct (we cannot honestly cost that bucket);
  the frontend communicates it clearly. Operators can narrow the range to isolate
  affected periods. Document this in apply so it is not mistaken for a bug.
- **Python bucketing on large ranges** → O(N) over sales+lines+gastos.
  **Mitigation**: bounded by the date filter; reporting path, not OLTP. SQL
  `date_trunc` is a documented future optimization (Decision 2).
- **Timezone bucketing** → ventas are `datetime` UTC, gastos are `date`.
  **Mitigation**: normalize both to a UTC calendar date before keying so the same
  period maps to the same key on both sides. Per project rule, DB is UTC and the
  UI converts to local; bucketing is defined on UTC for determinism.
- **Parallel work with C-17** → both touch `reporte/schemas.py`,
  `service.py`, `router.py`. **Mitigation**: C-18 only APPENDS new symbols and
  never edits C-17's; reviewers verify no C-17 handler/schema diff (Decision 1
  coexistence rule). Merge order is independent.
- **estado filter assumption** → only `cobrada` sales count as revenue, matching
  C-17. **Mitigation**: stated explicitly; if the business later wants pending
  sales included, it is a spec change, not a silent default.

## Migration Plan

1. Add `FinancieroPeriodoRow`, `ReporteFinancieroResponse`, `GroupBy` to
   `reporte/schemas.py` (append; do not edit C-17 schemas).
2. Add `reporte_financiero(...)` to `reporte/service.py` (tenant-scoped queries +
   per-bucket indicators reusing the `calcular_ganancia` cost contract).
3. Register `GET /reportes/financieros` in `reporte/router.py` with
   `Depends(require_role("reportes:read"))` (append; do not edit C-17 routes).
4. Add the frontend page, feature components, hook, and the
   `/reportes/financieros` route in `App.tsx`.
5. **No database migration.** **No new model.**

**Rollback**: remove the single new route registration (and the frontend route).
No data is mutated → zero data risk.

## Open Questions

All resolved by this design:
1. **Cost source** → C-12 `costo_unitario` snapshot via the `calcular_ganancia`
   contract; NULL-if-any-null per bucket (Decision 3). Never recomputed from
   current product cost.
2. **Coexistence with C-17** → same module/router, separate route, append-only,
   no edits to `/reportes/ventas` (Decision 1).
3. **group_by** → enum param, 422 on invalid, Python period-key bucketing
   (Decision 2).
4. **utilidad bruta / neta** → `ventas − costos` and `utilidad_bruta − gastos`,
   null-propagating (Decision 3).
5. **No migration** → confirmed; read-only over existing tables (Decision 5).
6. **Charting library** → reuse whatever C-16 dashboard uses; verified at apply.
