# Spec: reporte-ventas

Delta spec for C-17 — Reportes de ventas.
References: US-017, RN-REP-01, RN-REP-02, RN-REP-03, RN-SEG-01, RN-SEG-02.

---

## ADDED Requirements

### Requirement: List sales report with filters
The system SHALL expose `GET /reportes/ventas` that returns a paginated,
tabular list of **cobradas** sales for the authenticated user's empresa,
optionally filtered by date range and/or cliente.

Each row in the response SHALL include:
- `fecha` — UTC datetime of the sale
- `cliente_nombre` — display name of the client, or `"Público general"` when `cliente_id IS NULL`
- `productos` — comma-separated list of product names included in the sale
- `total_kilos` — sum of `detalle_venta.cantidad_kilos` for the sale (Decimal, 3 decimal places)
- `subtotal` — `venta.subtotal` (Decimal, 2 decimal places)
- `total` — `venta.total` (Decimal, 2 decimal places)
- `medios_pago` — comma-separated list of payment methods on the sale
- `ganancia_estimada` — result of `calcular_ganancia(lineas)`: a Decimal or `null`
  when any `detalle_venta.costo_unitario` is NULL (pre-snapshot historical rows)

ALL queries SHALL filter by `empresa_id` derived from the authenticated user's JWT
(RN-SEG-01, RN-SEG-02). Only sales with `estado = 'cobrada'` SHALL appear.

#### Scenario: Fetch all sales without filters
- **WHEN** an authenticated Administrador or Encargado calls `GET /reportes/ventas` with no query params
- **THEN** the system returns 200 with a paginated list of all `cobrada` sales for their empresa

#### Scenario: Filter by date range
- **WHEN** the request includes `fecha_desde` and/or `fecha_hasta` as ISO-8601 datetime strings
- **THEN** only sales where `venta.fecha >= fecha_desde` AND `venta.fecha <= fecha_hasta` are returned

#### Scenario: Filter by cliente_id
- **WHEN** the request includes `cliente_id` as a UUID
- **THEN** only sales linked to that cliente are returned
- **AND** the system SHALL verify that the cliente belongs to the same empresa; if not, 0 results are returned (not 403)

#### Scenario: No filters — public-general sales included
- **WHEN** no `cliente_id` filter is provided
- **THEN** sales with `cliente_id IS NULL` (public general) SHALL be included and displayed with `cliente_nombre = "Público general"`

#### Scenario: ganancia_estimada is null for pre-snapshot rows
- **WHEN** a sale has at least one `detalle_venta` where `costo_unitario IS NULL`
- **THEN** `ganancia_estimada` for that sale row SHALL be `null` (not zero, not an error)

#### Scenario: ganancia_estimada is a Decimal for fully-snapshotted rows
- **WHEN** all `detalle_venta` rows of a sale have `costo_unitario` set
- **THEN** `ganancia_estimada = Σ(importe) − Σ(cantidad_kilos × costo_unitario)` (Decimal, 2 d.p.)

#### Scenario: Pagination
- **WHEN** the request includes `skip` and `limit` query params
- **THEN** the response respects those bounds and includes a `total` count field

#### Scenario: Cross-tenant isolation
- **WHEN** a user from empresa A calls the endpoint
- **THEN** no sales from any other empresa appear, regardless of filter values

---

### Requirement: Export sales report as Excel (xlsx)
The system SHALL expose `GET /reportes/ventas/exportar?formato=xlsx` that applies
the same filter params as the list endpoint and returns a binary `.xlsx` file
with all matching rows (no pagination limit applied).

The xlsx file SHALL contain a single sheet named "Ventas" with one header row
followed by one data row per sale. Columns SHALL match RN-REP-03:
fecha, cliente, productos, kilos vendidos, subtotal, total, medio de pago, ganancia estimada.

Monetary values SHALL be formatted as numbers with 2 decimal places (not strings).
`ganancia_estimada` cells SHALL be empty (blank) when the value is `null`.
Kilos SHALL be formatted as numbers with 3 decimal places.

#### Scenario: Successful xlsx download
- **WHEN** an authenticated Administrador or Encargado calls `GET /reportes/ventas/exportar?formato=xlsx`
- **THEN** the response has status 200, `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, and a valid `.xlsx` binary body

#### Scenario: xlsx contains all rows matching filters
- **WHEN** filters are provided (date range, cliente_id)
- **THEN** the xlsx file contains exactly the rows that match those filters (no pagination cap)

#### Scenario: xlsx null ganancia renders as blank cell
- **WHEN** a sale row has `ganancia_estimada = null`
- **THEN** the corresponding xlsx cell is blank (empty), not "None" or "null"

---

### Requirement: Export sales report as CSV
The system SHALL expose `GET /reportes/ventas/exportar?formato=csv` that returns
a UTF-8 encoded CSV file with BOM (for Excel compatibility) containing all matching rows.

Columns SHALL match RN-REP-03 in this exact order:
`fecha,cliente,productos,kilos_vendidos,subtotal,total,medio_pago,ganancia_estimada`

Values SHALL use comma as delimiter. Strings with commas SHALL be quoted.
`ganancia_estimada` SHALL be an empty string when null.

#### Scenario: Successful CSV download
- **WHEN** an authenticated user calls `GET /reportes/ventas/exportar?formato=csv`
- **THEN** the response has status 200, `Content-Type: text/csv; charset=utf-8`, and UTF-8 BOM content

#### Scenario: CSV null ganancia renders as empty column
- **WHEN** a sale row has `ganancia_estimada = null`
- **THEN** the CSV cell for that row is empty (two consecutive commas or quoted empty string)

---

### Requirement: Export sales report as PDF
The system SHALL expose `GET /reportes/ventas/exportar?formato=pdf` that returns
a PDF document containing a table of matching rows with the same RN-REP-03 columns.

The PDF SHALL include:
- A header with the empresa name and the applied date range (if provided)
- A data table with RN-REP-03 columns
- A footer row with totals: sum of `total`, sum of `total_kilos`

#### Scenario: Successful PDF download
- **WHEN** an authenticated user calls `GET /reportes/ventas/exportar?formato=pdf`
- **THEN** the response has status 200, `Content-Type: application/pdf`, and a valid PDF binary body

#### Scenario: PDF null ganancia renders as em-dash
- **WHEN** a sale row has `ganancia_estimada = null`
- **THEN** the PDF cell shows `—` (em-dash), not blank or "None"

---

### Requirement: Export format validation
The system SHALL return 422 Unprocessable Entity when `formato` is not one of
`xlsx`, `csv`, or `pdf`.

#### Scenario: Invalid formato param
- **WHEN** `GET /reportes/ventas/exportar?formato=docx` is called
- **THEN** the system returns 422 with a validation error message listing valid formats

---

### Requirement: Access control for reportes endpoints
Only users with role `administrador` or `encargado` SHALL access
`GET /reportes/ventas` and `GET /reportes/ventas/exportar`.
Roles `cajero` and `vendedor` SHALL receive 403 Forbidden.

#### Scenario: Administrador can access report
- **WHEN** a user with role `administrador` calls `GET /reportes/ventas`
- **THEN** the system returns 200

#### Scenario: Encargado can access report
- **WHEN** a user with role `encargado` calls `GET /reportes/ventas`
- **THEN** the system returns 200

#### Scenario: Cajero is denied access
- **WHEN** a user with role `cajero` calls `GET /reportes/ventas`
- **THEN** the system returns 403

#### Scenario: Unauthenticated request is denied
- **WHEN** a request without a valid JWT calls `GET /reportes/ventas`
- **THEN** the system returns 401

---

### Requirement: Frontend reportes page with filter controls
The frontend SHALL provide a `/reportes` page accessible from the main navigation.

The page SHALL include:
- A date range picker for `fecha_desde` / `fecha_hasta`
- A cliente selector (dropdown/autocomplete from the empresa's client list), with a "All clients" default option
- A "Search" / "Apply filters" button that triggers `GET /reportes/ventas`
- A results table showing the RN-REP-03 columns
- Export buttons: "Export Excel", "Export PDF", "Export CSV" that call `GET /reportes/ventas/exportar?formato=<fmt>`
- A loading state while the request is in flight
- An empty state message when no results match

#### Scenario: User applies date range filter and sees results
- **WHEN** the user selects a date range and clicks "Apply"
- **THEN** the results table refreshes with rows matching that range

#### Scenario: User exports as xlsx
- **WHEN** the user clicks "Export Excel"
- **THEN** the browser downloads a `.xlsx` file named `ventas-<fecha_desde>-<fecha_hasta>.xlsx`

#### Scenario: User exports as PDF
- **WHEN** the user clicks "Export PDF"
- **THEN** the browser downloads a `.pdf` file named `ventas-<fecha_desde>-<fecha_hasta>.pdf`

#### Scenario: User exports as CSV
- **WHEN** the user clicks "Export CSV"
- **THEN** the browser downloads a `.csv` file named `ventas-<fecha_desde>-<fecha_hasta>.csv`

#### Scenario: Empty results state
- **WHEN** no sales match the applied filters
- **THEN** the table shows a "No results" message and export buttons are disabled

#### Scenario: ganancia_estimada null displayed in table
- **WHEN** a row has `ganancia_estimada = null`
- **THEN** the table cell shows `—` (em-dash) instead of blank or "null"
