# Spec: reportes-financieros

## ADDED Requirements

### Requirement: Financial indicators report endpoint

The system SHALL expose `GET /reportes/financieros` returning, per temporal
period, five financial indicators for the authenticated user's empresa:
`ventas`, `costos`, `gastos`, `utilidad_bruta`, and `utilidad_neta`
(RN-REP-05). The endpoint SHALL be read-only and MUST NOT mutate any data.

#### Scenario: Returns the five indicators per period
- **WHEN** an authenticated administrator requests `GET /reportes/financieros`
  with `group_by=mes` over a range that contains cobrada sales and registered gastos
- **THEN** the response contains one bucket per month in range, each with
  `ventas`, `costos`, `gastos`, `utilidad_bruta`, and `utilidad_neta` as
  Decimal-safe values

#### Scenario: Gross and net profit formulas
- **WHEN** a period bucket has `ventas = 1000.00`, `costos = 600.00`, `gastos = 150.00`
- **THEN** `utilidad_bruta` equals `400.00` (ventas − costos)
- **AND** `utilidad_neta` equals `250.00` (utilidad_bruta − gastos)

#### Scenario: Empty period
- **WHEN** a requested range contains no cobrada sales and no gastos
- **THEN** the response is an empty list of buckets (not an error)

### Requirement: Temporal grouping by day, week, month, year

The endpoint SHALL accept a `group_by` query parameter with the values
`dia`, `semana`, `mes`, and `anio`, and SHALL bucket all indicators by that
period (RN-REP-04). An invalid `group_by` value SHALL be rejected with HTTP 422.

#### Scenario: Group by day
- **WHEN** the request uses `group_by=dia` over a 3-day range with sales on two days
- **THEN** the response contains one bucket per day that has data, keyed by date

#### Scenario: Group by week
- **WHEN** the request uses `group_by=semana`
- **THEN** sales and gastos are aggregated into ISO-week buckets

#### Scenario: Group by year
- **WHEN** the request uses `group_by=anio` over a range spanning two calendar years
- **THEN** the response contains one bucket per year

#### Scenario: Invalid group_by rejected
- **WHEN** the request uses `group_by=trimestre`
- **THEN** the API responds with HTTP 422 and does not run any query

### Requirement: Cost of goods sold from immutable cost snapshot

The `costos` indicator SHALL be computed from the per-sale cost snapshot
`DetalleVenta.costo_unitario` using the same cost contract as
`calcular_ganancia` — cost of a line is `cantidad_kilos × costo_unitario`. The
system MUST NOT recompute costs from the current product cost, so historical
financials remain stable.

#### Scenario: Cost uses the sale-time snapshot, not current product cost
- **WHEN** a product's current cost changed after a sale was made
- **THEN** the `costos` indicator for the period of that sale uses the
  `costo_unitario` snapshot stored on the sale, not the product's current cost

#### Scenario: NULL cost snapshot is never treated as zero
- **WHEN** any cobrada sale in a period has a line with `costo_unitario IS NULL`
  (pre-snapshot historical sale)
- **THEN** that period's `costos`, `utilidad_bruta`, and `utilidad_neta` are
  reported as unavailable (null) rather than understating cost as zero
- **AND** the response signals the unavailability explicitly so the frontend can
  render it distinctly from a genuine `0.00`

### Requirement: Operating expenses from the gasto module

The `gastos` indicator SHALL be the sum of `gasto.importe` for the empresa,
bucketed into the same periods as the sales indicators, scoped by
`empresa_id` and the requested date range.

#### Scenario: Gastos aggregated per period
- **WHEN** two gastos of `100.00` and `50.00` fall in the same month bucket
- **THEN** that month's `gastos` indicator equals `150.00`

#### Scenario: Gastos affect net profit only
- **WHEN** a period has gastos but the same `ventas` and `costos` as another period without gastos
- **THEN** both periods share the same `utilidad_bruta`
- **AND** the period with gastos has a lower `utilidad_neta`

### Requirement: Multi-tenant isolation

Every query backing the report SHALL be scoped to the `empresa_id` derived from
the authenticated user's JWT. The report MUST NOT include any other empresa's
ventas, costos, or gastos.

#### Scenario: Tenant cannot see another tenant's financials
- **WHEN** empresa A and empresa B each have sales and gastos in the same period
- **AND** a user of empresa A requests the financial report
- **THEN** the indicators reflect ONLY empresa A's data
- **AND** none of empresa B's ventas, costos, or gastos appear

### Requirement: Access control

The endpoint SHALL require the `reportes:read` permission (administrador role per
the existing RBAC matrix). Requests without that permission SHALL receive HTTP 403.

#### Scenario: Authorized role allowed
- **WHEN** an administrator (holding `reportes:read`) requests the report
- **THEN** the request succeeds with HTTP 200

#### Scenario: Unauthorized role blocked
- **WHEN** a user without `reportes:read` requests the report
- **THEN** the API responds with HTTP 403 and no financial data is returned

### Requirement: Monetary precision and date handling

All monetary indicators SHALL be computed with `Decimal` precision (never
float) and serialized in a Decimal-safe representation. Dates SHALL be stored
and queried in UTC; period bucketing SHALL be deterministic for a fixed range.

#### Scenario: No floating-point drift
- **WHEN** indicators are summed across many sales and gastos
- **THEN** the returned totals match Decimal arithmetic exactly with no rounding drift

### Requirement: Financial reports frontend view

The frontend SHALL provide a financial-reports view that consumes
`GET /reportes/financieros` and presents the indicators as **comparative charts
and a table** (RN-REP-05 CA-3), with a `group_by` selector and a date-range
filter. The view SHALL be available only to authorized roles.

#### Scenario: Charts and table reflect the selected grouping
- **WHEN** the user selects `group_by=mes` and a date range
- **THEN** the view fetches the report and renders a comparative chart and a
  table with one row per month showing the five indicators

#### Scenario: Unavailable cost rendered distinctly
- **WHEN** a period returns null indicators because of a missing cost snapshot
- **THEN** the view renders that cell as a distinct "no disponible" marker,
  not as `0`
