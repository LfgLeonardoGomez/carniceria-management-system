# Proposal: C-18 — Reportes financieros

## Why

Administrators currently have a sales report (C-17) and a real-time dashboard
(C-16), but no way to see the **economic health of the business over time**:
revenue, cost of goods sold, operating expenses, gross profit and net profit
aggregated by day, week, month or year. US-018 (RN-REP-04, RN-REP-05) requires
this financial view so the administrator can evaluate profitability trends and
make pricing/spending decisions.

## What Changes

- New read-only endpoint **`GET /reportes/financieros`** returning, per period
  bucket, five financial indicators:
  - `ventas` — total revenue (sum of `total` of cobrada sales).
  - `costos` — cost of goods sold, from the immutable per-sale cost snapshot
    (`DetalleVenta.costo_unitario`), reusing the exact cost semantics of
    `calcular_ganancia`.
  - `gastos` — operating expenses from the `gasto` module (C-15).
  - `utilidad_bruta` = `ventas − costos`.
  - `utilidad_neta` = `utilidad_bruta − gastos`.
- A `group_by` query parameter with values `dia | semana | mes | anio` that
  buckets results temporally (RN-REP-04).
- Optional `fecha_desde` / `fecha_hasta` range filter, consistent with the
  existing `/reportes/ventas` filter contract.
- The endpoint lives in the **same `reporte` router and module as C-17**, but as
  a **separate route** — it does NOT touch or redefine `/reportes/ventas`. It
  reuses shared report infrastructure (router registration, `reportes:read`
  RBAC guard, the `calcular_ganancia` cost contract) without duplicating it.
- Strict multi-tenant isolation: every query scoped to `empresa_id` from the JWT.
- Frontend: a financial-reports view with comparative **charts and tables**
  (RN-REP-05 CA-3) backed by the new endpoint, with a `group_by` selector and
  date-range filter.
- No new database tables, columns, or migrations (read-only over existing
  `venta`, `detalle_venta`, `gasto`).

## Capabilities

### New Capabilities
- `reportes-financieros`: financial indicators report — revenue, COGS, operating
  expenses, gross profit and net profit aggregated by day/week/month/year,
  tenant-scoped, exposed via `GET /reportes/financieros` plus a charts-and-tables
  frontend view.

### Modified Capabilities
<!-- None. C-17's `/reportes/ventas` contract is unchanged. C-18 adds a sibling
     route in the same module; it does not alter any existing requirement. -->

## Impact

- **Backend** (`backend/src/modules/reporte/`):
  - `schemas.py` — add financial-report Pydantic schemas (period row + response,
    `extra='forbid'`, Decimal-as-string).
  - `service.py` — add `reporte_financiero(...)`: tenant-scoped aggregation of
    ventas/costos by period bucket + gastos by period bucket, joined into the
    five indicators using the `calcular_ganancia` cost contract.
  - `router.py` — register one new route `GET /reportes/financieros` guarded by
    `require_role("reportes:read")`.
- **Frontend** (`frontend/src/`): new financial-reports page/feature
  (filters, `group_by` selector, charts, comparative table, React Query hook),
  plus a route registration.
- **Dependencies**: relies on C-12 (ventas-cobro, cost snapshot + helper) and
  C-15 (gastos) — both DONE. A charting library may be added to the frontend
  (decided in design).
- **No migration**, **no new model**, **no change to `/reportes/ventas`**.

### Non-Goals (explicit)
- **Per-product / per-corte margin ranking** (most/least profitable products,
  margin by desposte cut) — that is **C-19 (rentabilidad)**, out of scope here.
- Export to xlsx/csv/pdf of the financial report (C-17 owns sales export; a
  financial export can be a future change if requested).
- Materialized views / read models / scheduled reports.
- Forecasting or projections.
