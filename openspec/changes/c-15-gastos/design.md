# Design: C-15 Gastos

## Architecture

Standard BASILE module pattern (matches venta, proveedor, compra):

```
backend/src/modules/gasto/
├── models.py    — Gasto SQLModel table (+ legacy CategoriaGasto)
├── schemas.py   — GastoCreate, GastoUpdate, GastoRead, GastoListResponse
├── service.py   — crear_gasto, listar_gastos, obtener_gasto, actualizar_gasto, eliminar_gasto
└── router.py    — FastAPI router with RBAC guards

backend/src/database/migrations/versions/
└── 000000000013_add_gasto_table.py

frontend/src/
├── shared/types/gasto.ts
├── features/gastos/api.ts
├── features/gastos/GastosGrid.tsx
├── features/gastos/GastoForm.tsx
├── stores/gastoStore.ts
└── pages/GastosPage.tsx
```

## Data Model

```
gasto
  id            UUID PK
  empresa_id    UUID FK → empresa.id  (NOT NULL, index)
  fecha         DATE                  (NOT NULL, index)
  categoria     STRING                (NOT NULL, index) — validated enum
  descripcion   STRING                (nullable)
  importe       NUMERIC(19,2)         (NOT NULL) — Decimal, never float
  medio_pago    STRING                (NOT NULL)
  created_at    DATETIME              (NOT NULL)
  updated_at    DATETIME              (NOT NULL)

Composite indexes: (empresa_id, fecha), (empresa_id, categoria)
```

## RBAC

- gastos:create → Admin, Encargado (POST, PUT, DELETE)
- gastos:read   → Admin, Encargado (GET)
- Cajero, Vendedor have NO access to gastos

## Alert seam (IN-04)

`service._check_alerta_gasto_elevado()` is a documented stub:
- When implemented: compare importe vs threshold in empresa.config
- Create notificacion record or emit event
- Currently a no-op

## Multi-tenant

`empresa_id` comes from `request.state.empresa_id` (set by auth middleware from JWT subclaim).
All queries filter by `Gasto.empresa_id == empresa_id`. No cross-tenant data leak possible.
