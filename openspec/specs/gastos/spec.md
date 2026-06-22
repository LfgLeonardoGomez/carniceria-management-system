# Spec: gastos

References: US-012, RN-FIN-01, RN-FIN-02, RN-FIN-03, RN-SEG-01, RN-SEG-02.

---

## Requirement: List gastos with filters

The system SHALL expose `GET /gasto` that returns a paginated list of
operational expenses (gastos) for the authenticated user's empresa,
optionally filtered by categoria and/or date range.

Each row in the response SHALL include:
- `id` — UUID of the gasto
- `fecha` — DATE of the expense
- `categoria` — fixed enum value (alquiler, empleados, luz, agua, gas, internet, combustible, impuestos, mantenimiento, insumos, otros)
- `descripcion` — optional text description of the expense
- `importe` — Decimal(19,2) amount of the expense
- `medio_pago` — payment method (e.g., efectivo, transferencia, cheque)
- `created_at` — creation timestamp
- `updated_at` — last modification timestamp

ALL queries SHALL filter by `empresa_id` derived from the authenticated user's JWT
(RN-SEG-01, RN-SEG-02).

### Scenario: Fetch all gastos without filters
- **WHEN** an authenticated Administrador or Encargado calls `GET /gasto` with no query params
- **THEN** the system returns 200 with a paginated list of all gastos for their empresa

### Scenario: Filter by categoria
- **WHEN** the request includes `categoria` query param with one of the valid enum values
- **THEN** only gastos with matching categoria are returned

### Scenario: Filter by date range
- **WHEN** the request includes `fecha_desde` and/or `fecha_hasta` as ISO-8601 date strings
- **THEN** only gastos where `fecha >= fecha_desde` AND `fecha <= fecha_hasta` are returned

### Scenario: Pagination
- **WHEN** the request includes `skip` and `limit` query params
- **THEN** the response respects those bounds and includes a `total` count field

### Scenario: Cross-tenant isolation
- **WHEN** a user from empresa A calls the endpoint
- **THEN** no gastos from any other empresa appear, regardless of filter values

---

## Requirement: Create a new gasto

The system SHALL expose `POST /gasto` that accepts a GastoCreate request body
and creates a new gasto record scoped to the authenticated user's empresa.

The request body SHALL include:
- `fecha` (DATE, required)
- `categoria` (enum string, required)
- `descripcion` (string, optional)
- `importe` (Decimal, required, MUST be > 0)
- `medio_pago` (string, required)

The response SHALL return 201 Created with the complete GastoRead record
(including id, created_at, updated_at).

### Scenario: Create gasto with valid data
- **WHEN** an authenticated Administrador or Encargado calls `POST /gasto` with valid GastoCreate
- **THEN** the system returns 201 with the new gasto record

### Scenario: categoria enum validation
- **WHEN** the request includes an invalid categoria value (not in the fixed enum)
- **THEN** the system returns 422 Unprocessable Entity with a validation error

### Scenario: importe must be positive
- **WHEN** `importe` is zero or negative
- **THEN** the system returns 422 with a validation error

### Scenario: gasto scoped to empresa
- **WHEN** a gasto is created
- **THEN** the `empresa_id` is automatically set from the authenticated user's JWT

---

## Requirement: Retrieve a single gasto by id

The system SHALL expose `GET /gasto/{id}` that returns a GastoRead record
for the gasto with the given UUID, if it belongs to the authenticated user's empresa.

### Scenario: Retrieve existing gasto
- **WHEN** an authenticated Administrador or Encargado calls `GET /gasto/{id}` with a valid id
- **THEN** the system returns 200 with the GastoRead record

### Scenario: gasto not found (cross-tenant check)
- **WHEN** the gasto_id does not exist or belongs to a different empresa
- **THEN** the system returns 404 Not Found

---

## Requirement: Update a gasto

The system SHALL expose `PUT /gasto/{id}` that accepts a GastoUpdate request body
and updates an existing gasto record.

The request body MAY include any of:
- `fecha`
- `categoria`
- `descripcion`
- `importe`
- `medio_pago`

The response SHALL return 200 OK with the updated GastoRead record.
Fields not included in the request body MUST remain unchanged.

### Scenario: Update gasto with partial data
- **WHEN** an authenticated Administrador or Encargado calls `PUT /gasto/{id}` with a partial GastoUpdate
- **THEN** the system returns 200 with the updated record

### Scenario: Update categoria validation
- **WHEN** `categoria` is provided and is invalid
- **THEN** the system returns 422

### Scenario: Update importe validation
- **WHEN** `importe` is provided and is <= 0
- **THEN** the system returns 422

### Scenario: gasto not found
- **WHEN** the gasto_id does not exist or belongs to a different empresa
- **THEN** the system returns 404 Not Found

---

## Requirement: Delete a gasto

The system SHALL expose `DELETE /gasto/{id}` that permanently removes a gasto record.

The system uses hard delete (no soft-delete) because gastos have no cross-module
dependencies (unlike ventas or stock movements).

### Scenario: Delete existing gasto
- **WHEN** an authenticated Administrador or Encargado calls `DELETE /gasto/{id}`
- **THEN** the system returns 204 No Content and the gasto is permanently removed

### Scenario: gasto not found
- **WHEN** the gasto_id does not exist or belongs to a different empresa
- **THEN** the system returns 404 Not Found

---

## Requirement: Access control for gasto endpoints

Only users with role `administrador` or `encargado` SHALL access
any gasto endpoint (GET, POST, PUT, DELETE).
Roles `cajero` and `vendedor` SHALL receive 403 Forbidden.

### Scenario: Administrador can create gasto
- **WHEN** a user with role `administrador` calls `POST /gasto`
- **THEN** the system returns 201 (if valid)

### Scenario: Encargado can manage gastos
- **WHEN** a user with role `encargado` calls any gasto endpoint
- **THEN** the system processes the request (201/200/204 if valid)

### Scenario: Cajero is denied access
- **WHEN** a user with role `cajero` calls any gasto endpoint
- **THEN** the system returns 403 Forbidden

### Scenario: Unauthenticated request is denied
- **WHEN** a request without a valid JWT calls any gasto endpoint
- **THEN** the system returns 401 Unauthorized

---

## Requirement: Gasto data model

Gastos are stored with the following schema:

```
gasto
  id            UUID PK
  empresa_id    UUID FK → empresa.id  (NOT NULL, indexed)
  fecha         DATE                  (NOT NULL, indexed)
  categoria     STRING                (NOT NULL, indexed)
  descripcion   STRING                (nullable)
  importe       NUMERIC(19,2)         (NOT NULL)
  medio_pago    STRING                (NOT NULL)
  created_at    DATETIME              (NOT NULL)
  updated_at    DATETIME              (NOT NULL)

Composite indexes: (empresa_id, fecha), (empresa_id, categoria)
```

The `categoria` field accepts only one of these fixed enum values:
- `alquiler`
- `empleados`
- `luz`
- `agua`
- `gas`
- `internet`
- `combustible`
- `impuestos`
- `mantenimiento`
- `insumos`
- `otros`

### Scenario: categoria is an enum, not a DB lookup table
- **WHEN** a gasto is created
- **THEN** the categoria value MUST be one of the 11 fixed values above
- **AND** the categoria is stored as a validated string, not a foreign key

### Scenario: importe uses Decimal precision
- **WHEN** importe is stored or retrieved
- **THEN** it is always a Decimal(19,2) value in the database
- **AND** Python code uses `decimal.Decimal` (never float)

### Scenario: Hard delete
- **WHEN** a gasto is deleted
- **THEN** it is permanently removed from the database (no soft-delete / is_deleted flag)

---

## Requirement: Alerta de gastos elevados (stub)

The backend SHALL include a documented stub function `_check_alerta_gasto_elevado()`
in the gasto service that allows future implementation of high-expense alerting.

The stub function:
- Takes a gasto importe and empresa configuration as parameters
- Currently performs no operation (no-op)
- Includes clear documentation that implementation (IN-04) will:
  - Compare importe against a threshold in `empresa.config`
  - Create a `notificacion` record when the threshold is exceeded
  - Or emit an event for a future alert engine

### Scenario: Stub implementation
- **WHEN** a gasto is created
- **THEN** the backend calls `_check_alerta_gasto_elevado()` but takes no action
- **AND** the function is documented for future alert engine integration

### Scenario: Alert engine is deferred
- **WHEN** future change IN-04 is implemented
- **THEN** the stub can be replaced with real logic without modifying the gasto create flow

---

## Requirement: Frontend gastos page

The frontend SHALL provide a `/gastos` page accessible from the main navigation
(if the user has `gastos:read` permission).

The page SHALL include:
- A date range picker for `fecha_desde` / `fecha_hasta`
- A categoria selector (dropdown) with a "All categories" default option
- A "Search" / "Apply filters" button that triggers `GET /gasto`
- A results table showing the gasto columns (fecha, categoria, descripcion, importe, medio_pago)
- An "Add gasto" button that opens a form for creating a new expense
- Edit / Delete buttons on each row
- A loading state while the request is in flight
- An empty state message when no results match

### Scenario: User applies date range filter
- **WHEN** the user selects a date range and clicks "Apply"
- **THEN** the results table refreshes with gastos matching that range

### Scenario: User applies categoria filter
- **WHEN** the user selects a categoria from the dropdown
- **THEN** the results table refreshes with gastos matching that categoria

### Scenario: User creates a new gasto
- **WHEN** the user clicks "Add gasto" and fills in the form
- **THEN** a `POST /gasto` request is sent and the new row appears in the table

### Scenario: User edits a gasto
- **WHEN** the user clicks Edit on a row and updates the form
- **THEN** a `PUT /gasto/{id}` request is sent and the row is updated

### Scenario: User deletes a gasto
- **WHEN** the user clicks Delete on a row
- **THEN** a `DELETE /gasto/{id}` request is sent and the row is removed from the table

### Scenario: Empty results state
- **WHEN** no gastos match the applied filters
- **THEN** the table shows a "No expenses found" message

---
