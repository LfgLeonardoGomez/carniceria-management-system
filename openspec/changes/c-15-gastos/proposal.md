# Proposal: C-15 Gastos

## Intent

Provide carnicería operators (Admin / Encargado) with a module to record, view, filter,
and manage operational expenses (gastos) at the empresa level.

## Scope

### In scope
- CRUD for gastos: POST /gasto, GET /gasto, GET /gasto/{id}, PUT /gasto/{id}, DELETE /gasto/{id}
- Fixed category enum (11 values): alquiler, empleados, luz, agua, gas, internet, combustible,
  impuestos, mantenimiento, insumos, otros
- Filters: by categoria, by date range (fecha_desde / fecha_hasta)
- Multi-tenant isolation: all queries scoped by empresa_id from JWT subclaim
- Alerta de gastos elevados: PLACEHOLDER seam only (IN-04, not implemented)
- Frontend: GastosGrid, GastoForm, GastosPage, gastoStore, gasto types

### Out of scope
- Alert engine (IN-04)
- Reporting / analytics
- Budget limits

## Why

C-15 enables operators to track operational costs alongside revenue from ventas,
supporting the P&L visibility that carnicería owners need.

## Key decisions

- Categories are a fixed Python set (not a DB lookup table) — simpler, no seed data needed.
  CategoriaGasto table pre-exists in DB but is legacy; new Gasto.categoria is a validated string.
- Hard delete for gastos (no soft-delete needed — gastos have no cross-module dependencies
  unlike ventas or stock movements).
- importe stored as Numeric(19,2) with Decimal in Python — no float.
- Alerta seam left as a documented stub function in service.py for IN-04.
