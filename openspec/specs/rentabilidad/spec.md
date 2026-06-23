# Spec: rentabilidad

## ADDED Requirements

### Requirement: Product margin ranking endpoint

The system SHALL expose `GET /rentabilidad/productos` returning a ranking of
products by their REAL transactional margin over a date range, for the
authenticated user's empresa (RN-RENT-01, US-019 CA-1/CA-2). The endpoint SHALL
be read-only and MUST NOT mutate any data. Each row SHALL include the product
identifier, product name, total ventas, total ganancia, and margen percentage.

#### Scenario: Returns one row per product with margin figures
- **WHEN** an authenticated administrator requests `GET /rentabilidad/productos`
  over a range that contains cobrada sales for two products
- **THEN** the response contains one row per product, each with `producto_id`,
  `nombre`, `ventas`, `ganancia`, and `margen_porcentaje` as Decimal-safe values

#### Scenario: Margin formula
- **WHEN** a product has `Σ(importe) = 1000.00` and
  `Σ(cantidad_kilos × costo_unitario) = 600.00` across the range
- **THEN** that product's `ganancia` equals `400.00` (ventas − costos)
- **AND** its `margen_porcentaje` equals `40.00` (ganancia / ventas × 100)

#### Scenario: Most-profitable ordering (default)
- **WHEN** the request omits the sort parameter (or uses `orden=mayor`)
- **THEN** rows are ordered by margin descending (most profitable first), so the
  first rows satisfy CA-1

#### Scenario: Least-profitable ordering
- **WHEN** the request uses `orden=menor`
- **THEN** rows are ordered by margin ascending (least profitable first),
  satisfying CA-2

#### Scenario: Top-N limit
- **WHEN** the request uses `top=5` over a range with more than five products
- **THEN** the response contains at most five rows, taken from the head of the
  requested ordering

### Requirement: Product margin uses the immutable cost snapshot

The product margin SHALL be computed from the per-sale cost snapshot
`DetalleVenta.costo_unitario` using the same cost contract as `calcular_ganancia`
— cost of a line is `cantidad_kilos × costo_unitario`. The system MUST NOT
recompute costs from the current product cost, so historical margins remain
stable.

#### Scenario: Margin uses sale-time cost, not current product cost
- **WHEN** a product's current cost changed after a sale was made
- **THEN** the product's `ganancia` and `margen_porcentaje` use the
  `costo_unitario` snapshot stored on each sale line, not the product's current
  cost

#### Scenario: NULL cost snapshot makes margin unavailable, never zero
- **WHEN** a product has at least one sale line with `costo_unitario IS NULL`
  (pre-snapshot historical sale) within the range
- **THEN** that product's `ganancia` and `margen_porcentaje` are reported as
  unavailable (null), NOT as zero or as inflated profit
- **AND** the response signals the unavailability explicitly so the frontend can
  render it distinctly from a genuine `0.00`

#### Scenario: Products with null margin are excluded from ranked ordering
- **WHEN** the ranking is ordered (by `mayor` or `menor`)
- **THEN** products whose margin is null are sorted deterministically AFTER all
  products with a known margin, so they never appear as "most" or "least"
  profitable on the basis of missing data

### Requirement: Cut margin endpoint

The system SHALL expose `GET /rentabilidad/cortes` returning the margin per
desposte cut (corte) over a date range, for the authenticated user's empresa
(RN-RENT-02, US-019 CA-3). The endpoint SHALL be read-only and MUST NOT mutate
any data. Margin per cut crosses the cut cost (`CorteDesposte.costo_final_por_kilo`)
against the average sale price of the linked product
(`CorteDesposte.producto_id` → `DetalleVenta.producto_id`).

#### Scenario: Returns margin per matched cut
- **WHEN** an authenticated administrator requests `GET /rentabilidad/cortes`
  over a range where a cut is linked to a product that has cobrada sales
- **THEN** the response includes a row for that cut with its cut type, product,
  `costo_por_kilo`, `precio_venta_promedio`, and `margen_porcentaje` as
  Decimal-safe values

#### Scenario: Cut margin formula
- **WHEN** a cut has `costo_final_por_kilo = 800.00` and the linked product has
  an average sale price of `1000.00` per kilo over the range
- **THEN** the cut's `margen_por_kilo` equals `200.00` (precio − costo)
- **AND** its `margen_porcentaje` equals `20.00` (margen / precio × 100)

#### Scenario: Cuts without a linked product are excluded from the cross
- **WHEN** a cut has `producto_id IS NULL`
- **THEN** that cut cannot be matched to any sale and SHALL be excluded from the
  result (it is not reported with a zero or null margin row)

#### Scenario: Linked product has no sales in range
- **WHEN** a cut is linked to a product that has no cobrada sales within the range
- **THEN** that cut's `precio_venta_promedio` is unavailable (null) and its
  `margen_porcentaje` is null — never computed from a zero price

### Requirement: Date range filtering

Both endpoints SHALL accept optional `fecha_desde` and `fecha_hasta` query
parameters and SHALL restrict the underlying **sales** to that range. The period
is defined by sale date (`Venta.fecha`), not by desposte date: a cut's cost is a
catalog-level figure (`CorteDesposte.costo_final_por_kilo`) that is not
time-bounded, so cuts are included whenever they have linked sales within the
range. Date handling SHALL be consistent with the rest of the system (UTC
storage, calendar-day inclusive bounds).

#### Scenario: Range narrows the result
- **WHEN** the same empresa has sales both inside and outside a requested range
- **THEN** only sales within `[fecha_desde, fecha_hasta]` contribute to the
  margin figures, for both productos and cortes

#### Scenario: No range returns all available data
- **WHEN** neither `fecha_desde` nor `fecha_hasta` is supplied
- **THEN** the endpoint aggregates over all cobrada sales for the empresa

### Requirement: General profitability is served by the existing financial report

The `rentabilidad` capability SHALL NOT introduce a dedicated general-period
profitability endpoint. US-019 CA-4 (rentabilidad general del período,
RN-RENT-03) is satisfied by the existing `GET /reportes/financieros` (C-18),
which already returns ventas, costos, gastos, utilidad bruta, and utilidad neta
per period. The profitability frontend view SHALL reuse that endpoint for the
general view rather than duplicate its logic.

#### Scenario: General profitability reuses the financial report
- **WHEN** the administrator opens the general profitability view
- **THEN** the data is sourced from `GET /reportes/financieros`, and no
  `/rentabilidad/general` route exists in the system

### Requirement: Multi-tenant isolation

Every query backing both endpoints SHALL be scoped to the `empresa_id` derived
from the authenticated user's JWT. The endpoints MUST NOT include any other
empresa's ventas, costos, productos, or cortes.

#### Scenario: Tenant cannot see another tenant's profitability
- **WHEN** empresa A and empresa B each have sales and desposte cuts in the same
  period
- **AND** a user of empresa A requests either profitability endpoint
- **THEN** the results reflect ONLY empresa A's data
- **AND** none of empresa B's products, cuts, or margins appear

### Requirement: Access control

Both endpoints SHALL require the `reportes:read` permission (administrador and
encargado roles per the existing RBAC matrix). Requests without that permission
SHALL receive HTTP 403.

#### Scenario: Authorized role allowed
- **WHEN** an administrator (holding `reportes:read`) requests either endpoint
- **THEN** the request succeeds with HTTP 200

#### Scenario: Unauthorized role blocked
- **WHEN** a user without `reportes:read` (e.g. cajero) requests either endpoint
- **THEN** the API responds with HTTP 403 and no profitability data is returned

### Requirement: Monetary precision

All monetary and margin values SHALL be computed with `Decimal` precision (never
float) and serialized in a Decimal-safe representation. Aggregations SHALL be
deterministic for a fixed range and dataset.

#### Scenario: No floating-point drift
- **WHEN** margins are summed and divided across many sales
- **THEN** the returned figures match Decimal arithmetic exactly with no rounding
  drift

### Requirement: Profitability frontend view

The frontend SHALL provide a profitability view that consumes
`GET /rentabilidad/productos` and `GET /rentabilidad/cortes` and presents the
data as **ranking tables and comparison charts**, with a date-range filter and a
sort/Top-N control for the product ranking. The view SHALL also surface general
profitability by consuming the existing `GET /reportes/financieros` (CA-4). The
view SHALL be available only to authorized roles, follow TypeScript strict mode
(no `any`), and use Decimal-safe handling for monetary values.

#### Scenario: Product ranking table and chart
- **WHEN** the user opens the product profitability tab and selects a date range
- **THEN** the view fetches `GET /rentabilidad/productos` and renders a ranking
  table plus a comparison chart, with a control to switch between most/least
  profitable and to limit Top-N

#### Scenario: Cut margin view
- **WHEN** the user opens the cut profitability tab
- **THEN** the view fetches `GET /rentabilidad/cortes` and renders per-cut
  margin in a table and a comparison chart

#### Scenario: Unavailable margin rendered distinctly
- **WHEN** a product or cut returns a null margin (missing cost snapshot or no
  sales)
- **THEN** the view renders that cell as a distinct "no disponible" marker, not
  as `0`
