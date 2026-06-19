# Proposal: Client Management (C-06)

## Why

BASILE needs a client registry to support differentiated pricing, loyalty tracking, and accounts receivable — core capabilities for a butcher shop SaaS. Without structured client data, the system cannot apply mayorista/especial pricing (RN-CLI-02) or manage cuentas corrientes (RN-CC-01). This change delivers the foundational client domain so downstream features (ventas, cuenta corriente, reportes) can operate on real customer records.

## What Changes

- **Backend**: Full CRUD REST API under `/clientes` with multi-tenant isolation.
- **Backend**: New endpoint `GET /clientes/{id}/historial` to list associated sales.
- **Backend**: `saldo_actual` field maintained as a snapshot from `CuentaCorriente` (full reconciliation logic in C-14).
- **Frontend**: Client grid with filters by tipo; client detail view showing profile, purchase history, and current balance.
- **Database**: New `cliente` table with migration; seed data for tipos de cliente.
- **Tests**: CRUD, historial, saldo computation, tenant isolation, RBAC enforcement.

## Capabilities

### New Capabilities
- `cliente-management`: CRUD operations for clients, including purchase history and account balance snapshot.

### Modified Capabilities
- (none — no existing spec-level requirements change)

## Impact

- `backend/src/modules/cliente/` — new models, schemas, router, service.
- `frontend/src/features/clientes/` — new pages, components, hooks.
- Database schema — new `cliente` table; migration required.
- RBAC matrix — Cajero and Administrador get CRUD on clientes; Encargado gets CRU; Vendedor has no access.
- Depends on C-03 (empresa-config) for tenant context and C-04 (usuarios-rbac) for permission enforcement.
