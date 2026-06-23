## Why

C-12 (ventas-cobro) already generates debt in a customer's current account when a sale is paid with `cuenta_corriente`, and reverses it on annulment. But there is no way to **register payments against that debt**, **consult a customer's movement history and balance**, or **produce a printable account statement**. The `cuenta_corriente` module router is a 3-line stub with no service layer. Shop operators cannot collect on outstanding debt nor see what each customer owes — the financing loop opened by C-12 has no closing half. This change adds the payment + read side of current accounts, completing US-015 (CA-2, CA-3, CA-4) on top of the existing debt-generation (CA-1, already delivered by C-12).

## What Changes

- **New current-account service layer** (`backend/src/modules/cuenta_corriente/service.py`) — currently missing.
- **`POST /cuentas-corrientes/{cliente_id}/pagos`** — register a partial or total payment. Atomically inserts a `tipo="pago"` movement, recomputes `saldo_resultante`, and updates the customer's `saldo_actual`, consistent with the C-12 debt convention.
- **`GET /cuentas-corrientes/{cliente_id}`** — paginated movement history (deuda + pago) plus current balance, using the project's standard `items/total/skip/limit` envelope.
- **`GET /cuentas-corrientes/{cliente_id}/estado-cuenta`** — exportable/printable account statement (RN-CC-02, CA-4), reusing the xlsx/csv/pdf export pattern from C-17/C-18.
- **Wire the router** into `main.py` under prefix `/cuentas-corrientes` (today it is an empty stub).
- **Frontend**: clients grid showing current balance, a current-account ficha (movement history + balance), a payment form, and a printable/downloadable account statement.
- **NOT changed**: the debt-on-sale logic in `venta/service.py` (C-12). This change reads and stays consistent with it; it does not duplicate or modify it.

## Capabilities

### New Capabilities
- `cuentas-corrientes`: Customer current-account management — registering payments against debt, consulting movement history and current balance, and producing an exportable/printable account statement. Debt-generation-per-sale is owned by the existing `ventas` capability (C-12) and only referenced here for consistency.

### Modified Capabilities
<!-- None. Debt generation lives in the ventas capability and is not having its requirements changed. -->

## Impact

- **New code**: `cuenta_corriente/service.py`, `cuenta_corriente/schemas.py`, expanded `cuenta_corriente/router.py`; `main.py` router registration; frontend `features/cuentas-corrientes/` + a page.
- **Existing tables**: `cuenta_corriente` (movements) and `cliente.saldo_actual` already exist (migration 012). No schema migration required for the first slice.
- **APIs**: 3 new endpoints under `/cuentas-corrientes`.
- **RBAC**: reuses existing `cuenta-corriente:read` (history, balance, statement) and `cuenta-corriente:update` (register payment) permissions — both already granted to `admin` and `encargado` (NOT `cajero`). Note: KB US-015 says "Administrador o Cajero"; the live RBAC matrix grants `encargado` not `cajero`. This discrepancy is surfaced for PO confirmation.
- **Dependencies**: depends on C-06 (cliente) and C-12 (ventas-cobro debt write). Export reuses `openpyxl` + `reportlab` already vendored by C-17.
- **Out of scope (non-goals)**: overdue-debt alerts/notifications (RN-CC-03, CA-5) — requires defining due-days (IN-04, unresolved); credit-limit enforcement on sale (RN-CLI-04, "pending to define"). Both deferred to a later change.
