## ADDED Requirements

### Requirement: Register payment against a customer's current account

The system SHALL allow an authorized user to register a payment (partial or total) against a customer's current account via `POST /cuentas-corrientes/{cliente_id}/pagos`. The operation SHALL be ACID: it MUST, within a single database transaction, insert a `tipo="pago"` movement, set that movement's `saldo_resultante` to the customer's balance after the payment, and update the customer's `saldo_actual`. The request body SHALL be a Pydantic model with `extra='forbid'` carrying at least `importe` (Decimal). All monetary values SHALL be Decimal with 2 decimal places; `float` MUST NOT be used.

#### Scenario: Total payment clears the balance
- **WHEN** a customer has `saldo_actual` of 1000.00 and an authorized user posts a payment of `importe` 1000.00
- **THEN** a `cuenta_corriente` movement of `tipo="pago"`, `importe` 1000.00, `saldo_resultante` 0.00 is created
- **AND** the customer's `saldo_actual` becomes 0.00
- **AND** the response returns the created movement and the new balance

#### Scenario: Partial payment reduces the balance
- **WHEN** a customer has `saldo_actual` of 1000.00 and an authorized user posts a payment of `importe` 300.00
- **THEN** a `tipo="pago"` movement with `saldo_resultante` 700.00 is created
- **AND** the customer's `saldo_actual` becomes 700.00

#### Scenario: Payment amount must be positive
- **WHEN** an authorized user posts a payment with `importe` of 0 or a negative value
- **THEN** the system rejects the request with HTTP 422
- **AND** no movement is created and the balance is unchanged

#### Scenario: Payment fails atomically on error
- **WHEN** registering a payment and the balance update cannot be persisted
- **THEN** the movement insert is rolled back as well
- **AND** neither a movement row nor a balance change is committed

#### Scenario: Payment for a non-existent customer is rejected
- **WHEN** an authorized user posts a payment for a `cliente_id` that does not exist in the caller's tenant
- **THEN** the system responds with HTTP 404
- **AND** no movement is created

### Requirement: Overpayment handling

The system SHALL define a deterministic rule for payments that exceed the outstanding balance. In the first slice, the system SHALL reject a payment whose `importe` is greater than the customer's current `saldo_actual` with HTTP 409, leaving the balance unchanged. (Credit balances / overpayment as advance are a documented assumption pending PO confirmation; if approved later, this requirement is revised to allow `saldo_resultante` to go negative.)

#### Scenario: Overpayment is rejected in the first slice
- **WHEN** a customer has `saldo_actual` of 500.00 and an authorized user posts a payment of `importe` 800.00
- **THEN** the system responds with HTTP 409 and an explanatory message
- **AND** the customer's `saldo_actual` remains 500.00 and no movement is created

#### Scenario: Payment exactly equal to the balance is allowed
- **WHEN** a customer has `saldo_actual` of 500.00 and an authorized user posts a payment of `importe` 500.00
- **THEN** the payment is accepted and the balance becomes 0.00

### Requirement: Consult current-account history and balance

The system SHALL expose `GET /cuentas-corrientes/{cliente_id}` returning the customer's current-account movements (both `deuda` and `pago`) ordered by date, plus the current balance, using the project's standard paginated envelope (`items`, `total`, `skip`, `limit`) and including `saldo_actual`. Each movement SHALL expose `id`, `tipo`, `importe`, `saldo_resultante`, `venta_id`, and `fecha`.

#### Scenario: History returns debt and payment movements with balance
- **WHEN** a customer has a `deuda` of 1000.00 (from a credit sale) followed by a `pago` of 400.00
- **THEN** the history returns both movements ordered by date
- **AND** the response includes the current balance of 600.00
- **AND** the response uses the `items/total/skip/limit` envelope

#### Scenario: History for a customer with no movements
- **WHEN** an authorized user requests the history of a customer with no current-account activity
- **THEN** the system returns an empty `items` list, `total` 0, and balance 0.00

### Requirement: Debt-per-sale consistency with ventas (C-12)

The current-account capability SHALL treat the debt movement created by the sales-collection flow (C-12) as the source of debt. When a sale is paid with `cuenta_corriente`, a `tipo="deuda"` movement and the corresponding `saldo_actual` increase are produced by the `ventas` capability; the current-account capability SHALL NOT duplicate this logic and SHALL compute balances and history consistently with those movements.

#### Scenario: Credit sale produces a debt movement visible in history
- **WHEN** a sale is collected with medio_pago `cuenta_corriente` for a customer (C-12 flow)
- **THEN** a `tipo="deuda"` movement linked to the `venta_id` appears in that customer's current-account history
- **AND** the customer's `saldo_actual` reflects the added debt

#### Scenario: A subsequent payment composes with the sale-generated debt
- **WHEN** a customer has a `deuda` movement from a credit sale and an authorized user registers a `pago`
- **THEN** the payment's `saldo_resultante` is computed from the balance left by the debt movement
- **AND** the resulting `saldo_actual` equals debt minus payment

### Requirement: Exportable account statement

The system SHALL expose `GET /cuentas-corrientes/{cliente_id}/estado-cuenta` that returns the customer's account statement as a downloadable file (RN-CC-02, CA-4), reusing the export approach established by C-17/C-18. The endpoint SHALL accept a `formato` query parameter (`xlsx`, `csv`, `pdf`) and SHALL set the appropriate content type and download filename. The statement SHALL include the customer's movements (date, tipo, importe, saldo_resultante) and the current balance.

#### Scenario: Export the account statement as PDF
- **WHEN** an authorized user requests `estado-cuenta` with `formato=pdf` for a customer with movements
- **THEN** the system returns a PDF file download with the movements and the current balance
- **AND** the content type is `application/pdf`

#### Scenario: Export the account statement as csv
- **WHEN** an authorized user requests `estado-cuenta` with `formato=csv`
- **THEN** the system returns a CSV file download containing all movements
- **AND** the content type is `text/csv; charset=utf-8`

#### Scenario: Unsupported export format is rejected
- **WHEN** an authorized user requests `estado-cuenta` with an unsupported `formato`
- **THEN** the system responds with HTTP 422

### Requirement: Tenant isolation of current accounts

Every current-account operation SHALL be scoped to the caller's `empresa_id` (sourced from the authenticated request, never from the client body). A user SHALL NOT register a payment for, nor read the history or statement of, a customer belonging to another tenant. Payments and balances MUST NEVER cross tenants.

#### Scenario: Cannot register a payment for another tenant's customer
- **WHEN** a user authenticated for tenant A posts a payment for a customer that belongs to tenant B
- **THEN** the system responds with HTTP 404 (the customer is not visible in tenant A)
- **AND** no movement is created in either tenant

#### Scenario: History is filtered to the caller's tenant
- **WHEN** a user authenticated for tenant A requests the history of a customer in tenant B
- **THEN** the system responds with HTTP 404
- **AND** no tenant B movement data is returned

### Requirement: Authorization of current-account operations

Reading current-account history, balance, and the account statement SHALL require the `cuenta-corriente:read` permission. Registering a payment SHALL require the `cuenta-corriente:update` permission. Requests without the required permission SHALL be rejected with HTTP 403.

**RBAC grant (PO Decision 2026-06-23):** Both `cuenta-corriente:read` and `cuenta-corriente:update` SHALL be granted to **admin**, **encargado**, and **cajero** roles. This aligns with KB US-015 ("Administrador o Cajero") and supersedes the previous live matrix which omitted cajero.

#### Scenario: User without update permission cannot register a payment
- **WHEN** a user whose role lacks `cuenta-corriente:update` posts a payment
- **THEN** the system responds with HTTP 403
- **AND** no movement is created

#### Scenario: User without read permission cannot view history
- **WHEN** a user whose role lacks `cuenta-corriente:read` requests the history
- **THEN** the system responds with HTTP 403
