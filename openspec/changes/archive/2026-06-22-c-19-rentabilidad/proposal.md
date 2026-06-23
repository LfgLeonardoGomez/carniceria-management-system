## Why

The administrator can already see financial indicators per period (C-18
`GET /reportes/financieros`) and product volume rankings by kilos (C-16
`/dashboard/rankings`), but the system has no view of **real transactional
margin**: which products and which desposte cuts actually make money. US-019
asks the administrator to "ajustar precios y enfocarme en lo más rentable",
which requires margin computed from real sales and their cost snapshots — not
from the catalog `Producto.margen` field (a static price-vs-cost figure) and not
from kilos sold. This change delivers that missing profitability view so pricing
decisions are grounded in transactional reality.

## What Changes

- Add **`GET /rentabilidad/productos`** — ranks products by REAL transactional
  margin over a date range (highest margin = most profitable, lowest = least),
  with optional sort direction and top-N. Implements US-019 CA-1 and CA-2,
  applies RN-RENT-01.
- Add **`GET /rentabilidad/cortes`** — margin per desposte cut, crossing
  `CorteDesposte.costo_final_por_kilo` against the average sale price of the
  linked product. Implements US-019 CA-3, applies RN-RENT-02.
- Add a new read-only `rentabilidad` backend module (router + service + schemas),
  mirroring the structure of the existing `reporte` and `dashboard` modules. No
  new DB tables, no models, no migration — it only reads `venta` and `desposte`
  data.
- Add a frontend profitability view: ranking tables, comparison charts, and a
  date-range filter, consuming the two new endpoints.
- **NO new endpoint for general profitability.** US-019 CA-4 (rentabilidad
  general del período, RN-RENT-03) is already satisfied by the EXISTING
  C-18 `GET /reportes/financieros` (ventas, costos, gastos, utilidad bruta/neta
  with grouping and date range). The frontend profitability view links to that
  endpoint for CA-4; no `/rentabilidad/general` route is built (avoids
  duplication).

## Capabilities

### New Capabilities
- `rentabilidad`: Read-only profitability analysis over real sales and desposte
  data — product margin ranking and per-cut margin, scoped per tenant, with
  Decimal precision and explicit NULL-margin handling for pre-snapshot sales.

### Modified Capabilities
<!-- None. C-18 reportes-financieros already covers CA-4; it is reused as-is,
     not modified. No existing spec's requirements change. -->

## Impact

- **New backend module**: `backend/src/modules/rentabilidad/`
  (`router.py`, `service.py`, `schemas.py`, `__init__.py`).
- **Router registration**: `backend/src/main.py` adds
  `rentabilidad_router` under prefix `/rentabilidad` with `reportes:read`.
- **Reused primitives (not reimplemented)**:
  - `calcular_ganancia` semantics from `backend/src/modules/venta/service.py`
    (NULL `costo_unitario` → margin None, never zero).
  - `DetalleVenta.costo_unitario` cost snapshot (`venta/models.py`).
  - `CorteDesposte.costo_final_por_kilo` + `CorteDesposte.producto_id`
    bridge (`desposte/models.py`).
- **RBAC**: reuses the existing `reportes:read` permission (administrador and
  encargado already hold it). No new permission added.
- **Frontend**: new view under `frontend/src/features/rentabilidad/` plus a page
  under `frontend/src/pages/`, consuming the two endpoints via React Query.
- **Dependencies satisfied**: C-09 desposte, C-12 ventas, C-15 gastos.
- **Out of scope**: `/rentabilidad/general` (covered by C-18), any write
  operation, any change to the catalog `Producto.margen` field.
