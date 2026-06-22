# Design: C-17 — Reportes de ventas

## Context

The `reporte` module currently contains only a stub: an empty `APIRouter` in
`router.py` and a `# TODO` `models.py`. No domain logic exists yet.

C-12 (ventas-cobro) is complete and provides:
- `Venta` / `DetalleVenta` / `PagoVenta` SQLModel tables with the schema
  `detalle_venta.costo_unitario` (nullable Decimal — cost snapshot at sale time).
- `calcular_ganancia(lineas: List[DetalleVenta]) -> Optional[Decimal]` in
  `src.modules.venta.service` — reusable profit helper; returns `None` if any
  line has `costo_unitario IS NULL`.
- Indexes: `ix_venta_empresa_id_fecha`, `ix_venta_empresa_id_cliente_id`,
  `ix_venta_empresa_id_estado` covering all filter combinations.

The `Cliente` model exposes `nombre`, `apellido`, `razon_social` for display names.
`Producto` exposes `nombre` for the products column.

## Goals / Non-Goals

**Goals:**
- `GET /reportes/ventas` — paginated tabular report with filters (date range, cliente).
- `GET /reportes/ventas/exportar?formato=xlsx|csv|pdf` — binary file download.
- Frontend `/reportes` page: filter panel, table preview, export buttons.
- Multi-tenant isolation: every query scoped to `empresa_id` from JWT.
- Profit column uses the existing `calcular_ganancia` helper; no new cost logic.

**Non-Goals:**
- Scheduled reports, email delivery, or stored files.
- Read-model / materialized views (deferred to a future change if needed).
- Financial reports grouped by period (C-18), or product rentability (C-19).
- Frontend charting or graphs (those belong to C-16 dashboard).

## Decisions

### Decision 1: Export generation in the backend

**Chosen**: All three export formats (xlsx, csv, pdf) are generated in the
FastAPI backend via a single endpoint `GET /reportes/ventas/exportar?formato=<fmt>`.

**Rationale**: Backend generation guarantees data consistency (one SQL query,
one authoritative rendering), simplifies auth (the access-control dependency is
already in FastAPI), and avoids duplicating the row-assembly logic in the
frontend. The report set is bounded by the filter so payload size is manageable.

**Alternatives considered**:
- *Frontend generation (SheetJS/jsPDF)*: would require shipping the full dataset
  JSON to the browser and re-assembling. Chosen against because it duplicates
  the aggregation logic, exposes larger JSON payloads, and complicates future
  server-side paging or streaming.

**Libraries**:
- xlsx: `openpyxl` (pure-Python, no native deps, well-maintained)
- csv: Python stdlib `csv` module with UTF-8 BOM
- pdf: `reportlab` (mature, no system-level font deps for basic tables)

### Decision 2: One list endpoint + one export endpoint (with `formato` param)

**Chosen**: Two routes under `/reportes/ventas`:
- `GET /reportes/ventas` — JSON list (paginated)
- `GET /reportes/ventas/exportar?formato=xlsx|csv|pdf` — file download

**Rationale**: Keeps the filter contract (query params) identical for both
routes. The export route ignores `skip`/`limit` and runs without a pagination
cap. A single `formato` discriminator avoids three nearly-identical route
handlers.

**Alternatives considered**:
- Three separate export routes (`/exportar/xlsx`, `/exportar/csv`, `/exportar/pdf`):
  more explicit URLs but higher handler duplication. Rejected.

### Decision 3: Row granularity — one row per venta (not per detalle_venta)

**Chosen**: One row per `Venta`. The "productos" column is a comma-separated
aggregation of product names; "kilos vendidos" is the sum of
`detalle_venta.cantidad_kilos` for that venta; "medio de pago" aggregates
`pago_venta.medio_pago` values.

**Rationale**: RN-REP-03 lists these as columns on a *venta* row, not a
*detalle* row. Aggregating in SQL with `GROUP BY venta.id` keeps the result
set one-to-one with ventas and avoids N×M row explosion for multi-product,
multi-payment-method sales.

**SQL aggregation pattern** (conceptual):
```sql
SELECT
  v.id,
  v.fecha,
  v.cliente_id,
  COALESCE(c.nombre || ' ' || c.apellido, c.razon_social, 'Público general') AS cliente_nombre,
  STRING_AGG(DISTINCT p.nombre, ', ' ORDER BY p.nombre)  AS productos,
  SUM(dv.cantidad_kilos)                                  AS total_kilos,
  v.subtotal,
  v.total,
  STRING_AGG(DISTINCT pv.medio_pago, ', ')               AS medios_pago
FROM venta v
LEFT JOIN cliente c ON c.id = v.cliente_id
JOIN detalle_venta dv ON dv.venta_id = v.id
JOIN producto p ON p.id = dv.producto_id
LEFT JOIN pago_venta pv ON pv.venta_id = v.id
WHERE v.empresa_id = :empresa_id
  AND v.estado     = 'cobrada'
  -- optional filters
GROUP BY v.id, v.fecha, v.cliente_id, cliente_nombre, v.subtotal, v.total
ORDER BY v.fecha DESC
```

`calcular_ganancia` is called **in Python** after loading `detalle_venta` rows
(not in SQL) to reuse the existing tested helper.

### Decision 4: ganancia_estimada computed in Python, not in SQL

**Chosen**: After the SQL aggregation query, load `detalle_venta` rows per
venta (via `selectinload` already done for the list endpoint) and call
`calcular_ganancia(venta.detalles)` to populate the field.

**Rationale**: The `calcular_ganancia` helper in `venta/service.py` already
encodes the correct NULL-propagation semantics (if any line lacks a cost
snapshot, the profit is `None`, not zero). Re-implementing this in SQL would
risk divergence between the list endpoint and any future usage of the helper.

**Performance note**: For large result sets the O(N) Python loop is acceptable
because (a) the query is bounded by filters and (b) this is a reporting
endpoint not a hot OLTP path. If profiling reveals a bottleneck, a future
change can push the aggregation to SQL using a CASE WHEN expression.

### Decision 5: Client-name display for public-general sales

**Chosen**: When `venta.cliente_id IS NULL`, the `cliente_nombre` field
returns the string `"Público general"`. When a client exists, the display
name is derived as:
- `razon_social` if set (B2B clients)
- Otherwise `nombre || ' ' || apellido`

**Rationale**: Consistent with `venta.tipo_cliente_al_momento = 'publico_general'`
that is already stored on the sale. The spec explicitly requires this label.

### Decision 6: Reporte module file layout

```
backend/src/modules/reporte/
├── __init__.py          (unchanged — empty)
├── models.py            (stays a stub — no new DB tables needed)
├── schemas.py           (NEW — Pydantic response + export schemas)
├── service.py           (NEW — query + calcular_ganancia wiring)
└── router.py            (REPLACE stub — two routes registered)
```

No new Alembic migration is needed because this change is read-only (no new
tables or columns).

### Decision 7: Frontend route and component structure

```
frontend/src/
├── pages/
│   └── ReportesVentasPage.tsx        (NEW — page component)
├── features/
│   └── reportes/
│       ├── ReportesFilters.tsx       (NEW — date range + cliente selector)
│       ├── ReportesTable.tsx         (NEW — results table)
│       └── useReportesVentas.ts      (NEW — data-fetch hook, React Query)
└── App.tsx                           (ADD /reportes route)
```

The export is triggered by an anchor-style download: the hook constructs the
`/reportes/ventas/exportar?formato=xlsx` URL with current filter params and
opens it via `window.location.href` or a hidden `<a download>` tag — no
additional fetch call needed, the browser handles the file download.

### Decision 8: Access control — role guard

**Chosen**: A FastAPI dependency `require_roles(["administrador", "encargado"])`
is used on both routes. If the role is not in the allowed set, the dependency
raises `HTTPException(403)`. This mirrors the role-guard pattern used in other
modules.

**Frontend**: The `/reportes` route is conditionally rendered in the nav only
for users with role `administrador` or `encargado`. A 403 response from the
API displays a "No autorizado" message.

## Risks / Trade-offs

- **STRING_AGG column length**: For sales with many products, the `productos`
  column could be long. Mitigation: truncate at render in the PDF if needed;
  the xlsx/csv store the full string.
  
- **reportlab font support**: `reportlab` requires explicit font registration for
  Spanish characters. Mitigation: use the built-in `Helvetica` or register a
  bundled font (e.g., `DejaVuSans`) as part of setup. Tests must verify accented
  characters render without `UnicodeEncodeError`.

- **Large exports without pagination**: A date range spanning many months
  could return thousands of rows. A future change can add a row cap (e.g., 10 000)
  with a warning. For now, the query is bounded by the filters; operators
  should use a reasonably narrow date range.

- **ganancia_estimada null for old sales**: Pre-C-12 sales (before the cost
  snapshot was introduced) will always show `null`. This is correct behavior,
  not a bug — documented in the spec. The frontend renders `—` to communicate
  "not available".

## Migration Plan

1. Add `openpyxl`, `reportlab` to `backend/requirements.txt`.
2. Implement `reporte/schemas.py`, `reporte/service.py`, `reporte/router.py`.
3. Register the reporte router in `main.py` (or wherever module routers are
   aggregated — check existing pattern in `src/app.py` or `main.py`).
4. Add frontend page, feature components, and route in `App.tsx`.
5. No database migrations needed.

**Rollback**: Remove the two routes from the router registration. No data is
mutated, so rollback has zero data risk.

## Open Questions

All open questions from the proposal are resolved by this design:

1. **Ganancia source**: Uses `DetalleVenta.costo_unitario` snapshot via the
   existing `calcular_ganancia` helper. Pre-snapshot rows return `null`.
2. **Export location**: Backend (Decision 1).
3. **Public general**: Included in unfilitered report; displayed as "Público general" (Decision 5).
4. **Row granularity**: One row per venta (Decision 3).
5. **Pagination vs. export**: List endpoint paginates; export endpoint returns
   full result set without limit (Decision 2).
