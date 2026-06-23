## Context

C-12 (ventas-cobro) already wrote half of the current-account domain:

- Table `cuenta_corriente` (movements) and `cliente.saldo_actual` exist via Alembic migration `000000000012`.
- `venta/service.py` (cobro path) inserts a `tipo="deuda"` movement when a sale is paid with `cuenta_corriente`, computing `nuevo_saldo = (cliente.saldo_actual + venta.total).quantize(Decimal("0.01"))`, setting the movement's `saldo_resultante = nuevo_saldo`, and updating `cliente.saldo_actual`.
- On sale annulment it writes a `tipo="pago"` reversal movement and decreases `saldo_actual` symmetrically.

So the **authoritative running balance is `cliente.saldo_actual`** (Decimal). Each `cuenta_corriente` row stores `saldo_resultante` as the balance snapshot *after that movement*. The `cuenta_corriente` module today is a stub: `router.py` has 3 lines, no `service.py`, no `schemas.py`, and the router is not wired into `main.py`.

This change implements the payment + read side, staying byte-for-byte consistent with the C-12 convention. Governance level is HIGH (money: balances and payments), so atomicity, tenant isolation, and Decimal precision are first-class.

Reference patterns to mirror:
- `cliente/router.py` — request.state tenant pattern, `require_role(...)` dependencies, paginated envelope.
- `rentabilidad/router.py` — `current_user.empresa_id` from JWT, read-only RBAC gating.
- `reporte/router.py` + `reporte/service.py` — export pattern: `_CONTENT_TYPE_MAP`, `StreamingResponse`, `generar_xlsx` (openpyxl), `generar_csv` (csv stdlib), `generar_pdf` (reportlab). Reuse this for `estado-cuenta`.

## Goals / Non-Goals

**Goals:**
- Register partial/total payments atomically, consistent with the C-12 debt convention.
- Read movement history + current balance (paginated envelope).
- Export/print an account statement in xlsx/csv/pdf (reusing C-17/C-18 mechanics).
- Strict tenant isolation; Decimal money; ACID payment.

**Non-Goals:**
- Overdue-debt alerts/notifications (RN-CC-03, CA-5) — blocked on due-days definition (IN-04). Out of this slice.
- Credit-limit enforcement on sale (RN-CLI-04, "pending to define in v1.0"). Out of scope.
- Modifying or duplicating the C-12 debt-generation logic. Referenced only.
- No new Alembic migration (table already exists). If overpayment-as-credit is later approved, a follow-up may relax a NOT NULL / add a constraint — explicitly deferred.

## Decisions

### Decision 1 — `saldo_resultante` is a stored running-balance snapshot; concurrency via row lock

`cuenta_corriente.saldo_resultante` is NOT NULL and already populated by C-12, so it is **stored, not computed**. The invariant: `saldo_resultante` of a movement = customer balance immediately after that movement, and `cliente.saldo_actual` = the latest movement's `saldo_resultante`.

To keep concurrent payments consistent, the payment transaction MUST read the customer row `WITH FOR UPDATE` (SQLAlchemy `select(Cliente).with_for_update()`) before computing the new balance, then insert the movement and update `saldo_actual` inside the same transaction. This serializes concurrent payments for the same customer and prevents two payments from reading the same stale `saldo_actual`.

*Alternatives considered:* (a) recompute balance from the movement log on every read — rejected: C-12 already maintains `saldo_actual` and `saldo_resultante`; recomputing would diverge from the established source of truth and risk inconsistency. (b) optimistic locking with a version column — rejected: adds a schema migration for marginal benefit at expected low concurrency per customer; `FOR UPDATE` is simpler and correct.

**Answer to Q1:** Stored running balance (column already exists and is fed by C-12). Invariant defined above. Concurrency handled by `SELECT ... FOR UPDATE` on the `cliente` row inside the ACID payment transaction + deterministic ordering by `fecha` for history.

### Decision 2 — Overpayment rejected in the first slice (assumption pending PO)

The KB has no explicit rule on overpayment. RN-CC-01 only requires "registrar pagos". RN-CLI-04 (limit) is "pending to define". To stay safe in a money domain, the first slice **rejects** a payment greater than `saldo_actual` with HTTP 409 and leaves the balance untouched. Payment exactly equal to the balance is allowed (clears to 0.00). A negative/zero `importe` is a 422 (Pydantic validation, `gt=0`).

*Alternatives considered:* allow overpayment → negative `saldo_resultante` representing a credit/advance. This is plausible retail behavior but introduces credit-balance semantics (how is it consumed by the next sale? does C-12 need to read it?) that ripple into the ventas flow and are not specified. Deferring is the lower-risk call.

**Answer to Q2:** First slice rejects overpayment (409). Equal-to-balance allowed. This is an **ASSUMPTION requiring PO confirmation** — if the PO wants advance/credit balances, it becomes a follow-up that touches both this module and the C-12 cobro path.

### Decision 3 — `estado-cuenta` reuses the C-17/C-18 export trio (xlsx/csv/pdf)

`estado-cuenta` is the printable/exportable view of the same movements as the history endpoint, plus a header (customer + balance). It reuses the exact mechanics already in `reporte/service.py`: `_CONTENT_TYPE_MAP`, `StreamingResponse`, openpyxl/csv/reportlab generators. Default `formato=pdf` (the "printable" interpretation of RN-CC-02). No new dependency — `openpyxl` and `reportlab` are already vendored by C-17.

*Alternatives considered:* HTML-only printable view (browser print) — rejected: C-17/C-18 set the project precedent for server-generated downloads; consistency wins and gives a real file artifact. CSV-only — rejected: CA-4 says "exportable/imprimible"; PDF is the natural printable format.

**Answer to Q3:** Reuse C-17/C-18 export approach with `formato` ∈ {xlsx, csv, pdf}, default pdf. Minimal first slice: same three formats already supported elsewhere, no bespoke templating engine.

### Decision 4 — Module layout and RBAC

Mirror existing modules: `cuenta_corriente/{router,service,schemas}.py`, wired into `main.py` at prefix `/cuentas-corrientes`. Service functions are `async` and receive `db: AsyncSession`, `empresa_id`, `current_user`. Pydantic request/response models use `extra='forbid'`; money fields are `Decimal`.

RBAC: reuse the **already-existing** `cuenta-corriente:read` (history, balance, estado-cuenta) and `cuenta-corriente:update` (register payment) permissions. Both are granted today to `admin` and `encargado`, NOT to `cajero`. **KB discrepancy:** US-015 says "Administrador o Cajero" but the live `PERMISSION_MATRIX` grants `encargado` instead of `cajero`. We follow the live matrix (it is the source of truth in code) and surface the discrepancy as an open question for the PO. No RBAC matrix change in this slice.

## Risks / Trade-offs

- **Inconsistency with C-12 quantization** → Mitigation: use the identical `.quantize(Decimal("0.01"))` and `tipo="pago"` convention as `venta/service.py`; tests assert a credit sale + payment compose to the right `saldo_actual`.
- **Concurrent payments racing on `saldo_actual`** → Mitigation: `SELECT ... FOR UPDATE` on the `cliente` row inside the transaction (Decision 1). Note: the table has no DB CHECK enforcing `saldo_actual` ≥ 0; integrity is enforced at the service layer (and by overpayment rejection).
- **Tenant leak via `cliente_id` in path** → Mitigation: every query filters by `empresa_id` from the request/JWT; a foreign-tenant `cliente_id` resolves to 404, never 403, so existence is not leaked. Dedicated multi-tenant test.
- **Overpayment decision may be reversed by PO** → Mitigation: isolated as a single service rule + spec requirement; reversing it is localized.
- **History pagination ordering** → Mitigation: order by `fecha` (then `created_at` as tiebreaker) deterministically; envelope matches the project standard (`items/total/skip/limit`).
- **Export volume** → statements fetch all movements (no pagination), like C-17 exports; acceptable for per-customer scope.

## Migration Plan

No DB migration required — `cuenta_corriente` and `cliente.saldo_actual` already exist (migration 012). Deployment is purely additive code (new service/schemas, expanded router, `main.py` registration, frontend). Rollback = revert the code; no data migration to undo. If overpayment-as-credit is later approved, that follow-up evaluates whether any column/constraint change is needed.

## Open Questions

1. **Overpayment policy (PO):** reject (first-slice default) vs. allow advance/credit balance? If allowed, define how credit is consumed by future sales (impacts C-12).
2. **RBAC role for payments (PO):** KB US-015 says "Cajero"; live matrix grants `admin` + `encargado` (not `cajero`). Which is correct — add `cuenta-corriente:*` to `cajero`, or update the KB? First slice follows the live matrix.
3. **Overdue alerts (IN-04):** due-days are undefined. Needed before RN-CC-03 / CA-5 can be specified. Deferred.
4. **estado-cuenta date range:** full history vs. date-bounded statement? First slice = full history; a `fecha_desde/fecha_hasta` filter can be added later mirroring the reportes endpoints.
