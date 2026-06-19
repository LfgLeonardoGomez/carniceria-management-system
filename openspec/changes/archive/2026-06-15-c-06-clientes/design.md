# Design: Client Management (C-06)

## Context

- The `cliente` domain is currently empty: `backend/src/modules/cliente/` has placeholder files, and `frontend/src/features/clientes/` is empty.
- C-03 (empresa-config) is complete, providing the tenant context (`empresa_id`) and base configuration.
- C-04 (usuarios-rbac) is complete, providing RBAC enforcement that this change will leverage.
- The database has no `cliente` table yet; an Alembic migration is required.
- Downstream changes (C-14 cuenta-corriente, C-09 ventas) depend on this schema.

## Goals / Non-Goals

**Goals:**
- Provide a full CRUD REST API for `cliente` under `/clientes` with strict multi-tenant isolation.
- Expose `GET /clientes/{id}/historial` that returns paginated sales for a client.
- Maintain `saldo_actual` as a snapshot on `cliente` (updated by C-14 ledger logic), exposed in read responses.
- Build a frontend grid with filtering by `tipo_cliente` and a detail view with profile + history + balance.
- Enforce RBAC: Administrador = CRUD, Encargado = CRU, Cajero = CRU, Vendedor = no access.
- Cover with TDD: CRUD, historial, saldo computation, tenant isolation.

**Non-Goals:**
- Full cuenta corriente ledger logic (debt creation, payment recording, balance reconciliation) — that belongs to C-14.
- Real-time computed `saldo_actual` from `CuentaCorriente` rows on every read; we use a snapshot column.
- Pricing engine or special-price overrides per client (RN-CLI-02 pricing is applied at sale time, not stored here).
- Email/SMS notifications to clients.
- Bulk import of clients.

## Decisions

### 1. SQLModel for ORM model
- **Rationale**: Consistent with C-03/C-04 stack. SQLModel 2.0 provides Pydantic validation + SQLAlchemy declarative mapping in one class.
- **Alternative**: Separate SQLAlchemy model + Pydantic schema. Rejected because it adds boilerplate without benefit in this domain.

### 2. `saldo_actual` as snapshot column on `cliente` table
- **Rationale**: C-14 will own the ledger. When a debt or payment is recorded, C-14 updates `cliente.saldo_actual`. This avoids expensive SUM queries on the hot path (historial reads) and keeps the client API fast.
- **Trade-off**: Risk of drift if C-14 misses an update. Mitigated by: (a) C-14 updates within the same transaction, (b) periodic reconciliation job (future), (c) `CuentaCorriente.saldo_resultante` serves as audit trail.
- **Alternative**: Computed property `SELECT SUM(...) FROM cuenta_corriente`. Rejected because it couples read performance to ledger size.

### 3. Endpoint structure: `/clientes` with nested `/historial`
- **Rationale**: Clean REST hierarchy. `GET /clientes` list, `POST /clientes` create, `GET /clientes/{id}` detail, `GET /clientes/{id}/historial` sales history.
- **Alternative**: `/historial-ventas?cliente_id={id}`. Rejected because it scatters client-related endpoints and weakens URL semantics.

### 4. Frontend: Zustand store for client list + React Query for server state
- **Rationale**: Zustand holds UI state (filters, selected client); React Query handles caching, pagination, and background refetch for server data. Pattern established in C-03.
- **Alternative**: Pure Zustand for everything. Rejected because it forces manual cache management.

### 5. Decimal precision for `saldo_actual` and `limite_cuenta_corriente`
- **Rationale**: Money precision. Backend uses `Decimal` (SQLAlchemy `Numeric(19,4)`). Frontend uses a decimal library (e.g., `decimal.js` or string-based) to avoid floating-point rounding.
- **Alternative**: Float/double. Rejected — violates project rule "NEVER usar float para dinero".

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| `saldo_actual` drift if C-14 logic is buggy | C-14 must update `cliente.saldo_actual` atomically within the same DB transaction. Reconciliation script to be added in C-14. |
| Historial endpoint performance for clients with thousands of sales | Paginate with cursor/limit-offset; index `(cliente_id, fecha)` on `venta`. |
| Tenant isolation bypass via forged `empresa_id` | All queries filtered by `current_user.empresa_id` from JWT claim; RLS policy on `cliente` as defense in depth. |
| CUIT validation (Argentine format) | Validate with regex `^\d{2}-\d{8}-\d{1}$` or `^\d{11}$` in Pydantic schema; normalize to 11 digits before storage. |

## Migration Plan

1. Generate Alembic migration for `cliente` table.
2. Run migration in dev/test environments.
3. Seed `tipo_cliente` enum values (publico_general, mayorista, especial) if not already present in app code.
4. Deploy backend; verify `/clientes` health.
5. Deploy frontend client feature.
6. No rollback concerns — additive schema change.

## Open Questions

1. Should we enforce CUIT uniqueness per `empresa_id`? **Decision**: Yes, unique constraint `(empresa_id, cuit)` where `cuit IS NOT NULL` to allow multiple clients without CUIT.
2. Should inactive clients (`activo = false`) appear in historial? **Decision**: Yes, historial is historical data; inactive clients still have past sales.
3. Should `GET /clientes` default filter exclude inactive? **Decision**: No — default shows all; explicit `?activo=false` or `?activo=true` filters if needed.
