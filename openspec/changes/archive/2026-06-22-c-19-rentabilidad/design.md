# Design: c-19-rentabilidad

## Context

US-019 needs profitability views grounded in real transactional data. Three
primitives already exist and are reused, not reimplemented:

- `calcular_ganancia(lineas) -> Optional[Decimal]` (`venta/service.py:90`):
  `ganancia = Σ(importe) − Σ(cantidad_kilos × costo_unitario)`; returns `None`
  if ANY line has `costo_unitario IS NULL`. This NULL-is-not-zero contract is a
  project invariant.
- `DetalleVenta.costo_unitario` (`venta/models.py`): nullable Decimal cost
  snapshot captured at sale time.
- `CorteDesposte.costo_final_por_kilo` + `CorteDesposte.producto_id`
  (`desposte/models.py`): the cut cost and the optional FK bridging a cut to a
  product, which is how cut margin reaches sale prices.

C-18 `GET /reportes/financieros` already computes general period profitability
(ventas/costos/gastos/utilidad bruta/neta), so CA-4 is covered by reuse.
C-16 `/dashboard/rankings` ranks by KILOS (volume), not margin, so the margin
ranking here is genuinely new. `Producto.margen` is a catalog field
(precio vs costo_por_kilo) and is intentionally NOT used — it is not the real
transactional margin.

The `reporte` module (C-17/C-18) is the structural template: a read-only module
with `router.py`, `service.py`, `schemas.py`, pure helper functions separated
from DB queries for unit-testing, Decimal everywhere, and `reportes:read` RBAC.

## Goals / Non-Goals

**Goals**
- Two read-only endpoints: `GET /rentabilidad/productos`, `GET /rentabilidad/cortes`.
- Margin from the real cost snapshot, preserving the NULL-is-not-zero invariant.
- Strict multi-tenant isolation (`empresa_id` first in every query).
- Frontend ranking tables + comparison charts + date-range filter, plus reuse of
  the financial report for CA-4.

**Non-Goals**
- No `/rentabilidad/general` endpoint (CA-4 = C-18 reuse).
- No new DB tables, models, migrations, or RBAC permissions.
- No change to `Producto.margen` or to any C-16/C-17/C-18 code.
- No write/mutation operations.

## Decisions

### Decision 1: New read-only `rentabilidad` module, mirroring `reporte`
Create `backend/src/modules/rentabilidad/` with `router.py`, `service.py`,
`schemas.py`, `__init__.py`. Register in `main.py` under prefix `/rentabilidad`
with `dependencies=auth_dep` and per-route `require_role("reportes:read")`,
exactly as `reporte_router` is wired.
- **Why over adding routes to `reporte`**: profitability is a distinct domain
  concept (US-019 vs US-017/US-018); a separate module keeps cohesion and avoids
  touching C-17/C-18 code. **Alternative considered**: extend `dashboard` —
  rejected, dashboard is volume/operational, not margin.

### Decision 2: Reuse the cost contract, not the `calcular_ganancia` function call shape
`calcular_ganancia` operates on one sale's lines. For the product ranking we need
per-`producto_id` aggregation across many sales. We mirror its EXACT contract in
a pure helper rather than calling it per sale:
- Aggregate per product: `ventas = Σ(importe)`,
  `costos = Σ(cantidad_kilos × costo_unitario)`.
- If ANY contributing line for a product has `costo_unitario IS NULL` →
  that product's `ganancia` and `margen_porcentaje` are `None` (never zero).
- `margen_porcentaje = ganancia / ventas × 100`, quantized to 2 d.p.; guard
  `ventas == 0` → margin `None`.
- **Why**: keeps the established invariant centralized in behavior while allowing
  grouped aggregation. **Alternative**: call `calcular_ganancia` once per sale and
  re-aggregate — rejected, it loses per-product granularity and double-handles
  NULL propagation.

### Decision 3: Pure helpers separated from DB queries (testability)
Following the C-18 pattern (`_build_buckets_financieros` is pure and unit-tested
without a DB), put the aggregation logic in pure functions
(`_ranking_productos(detalles) -> list[ProductoRentabilidadRow]`,
`_margen_cortes(cortes, detalles) -> list[CorteRentabilidadRow]`) that take
in-memory lists. The async service functions do the tenant-scoped queries and
call the pure helpers.
- **Why**: enables fast unit tests for the NULL/zero edge cases and ordering,
  plus integration tests with real PostgreSQL (testcontainers) for the queries.

### Decision 4: Cut margin uses average sale price of the linked product
Per RN-RENT-02, cut margin = cut cost vs sale price. The bridge is
`CorteDesposte.producto_id → DetalleVenta.producto_id`. We compute, per linked
product, the average sale price per kilo over the range
(`Σ(importe) / Σ(cantidad_kilos)`, guard zero kilos), then for each cut:
`margen_por_kilo = precio_venta_promedio − costo_final_por_kilo`,
`margen_porcentaje = margen_por_kilo / precio_venta_promedio × 100`.
- **Edge case (excluded)**: cuts with `producto_id IS NULL` cannot be matched →
  excluded from the result entirely.
- **Edge case (null margin)**: linked product with no sales in range →
  `precio_venta_promedio` and `margen_porcentaje` are `None` (never zero price).
- **Why average price**: a product can sell at different prices (público vs
  mayorista, discounts); the average over the range is the representative figure
  for a margin overview. **Alternative**: last price — rejected, not
  representative of the period.

### Decision 5: Ordering and Top-N for product ranking
`orden` query param (`mayor` default | `menor`) controls sort direction.
Products with `None` margin are sorted deterministically AFTER all known-margin
products regardless of direction, so missing data never appears as "most/least"
profitable. `top` (optional positive int) limits the head of the ordered list.
- **Why**: directly satisfies CA-1 (most) and CA-2 (least) from one endpoint;
  null-last keeps the invariant honest in the ranking.

### Decision 6: Decimal-safe schemas with explicit nullable margins
Pydantic `BaseModel` with `model_config = {"extra": "forbid"}`, mirroring
`reporte/schemas.py`. Monetary/margin fields are `Decimal` (serialize as strings).
`ganancia`, `margen_porcentaje`, `precio_venta_promedio` are `Optional[Decimal]`
so a missing snapshot or no-sales case is explicitly null in JSON, never zero.

### Decision 7: Date-range handling mirrors C-18
Reuse the calendar-day inclusive UTC bounds approach from
`reporte_financiero` (start-of-day lower bound, `< next_day` upper bound for the
`Venta.fecha` datetime column) so range semantics match the financial report the
frontend also consumes.

## Risks / Trade-offs

- **[Risk] NULL cost propagation hides whole products from the ranking head** →
  Mitigation: products with null margin are still returned (with null fields) and
  ordered last; the frontend renders a distinct "no disponible" marker so the gap
  is visible, not silently dropped.
- **[Risk] Cuts with `producto_id IS NULL` silently disappear** → Mitigation:
  documented behavior in the spec; acceptable because an unmatched cut has no
  sale price and cannot yield a meaningful margin. (Optional: surface a count of
  excluded cuts — deferred, not required by CA-3.)
- **[Risk] Average sale price blends público/mayorista prices** → Accepted
  trade-off (Decision 4); the figure is an overview, not an invoice.
- **[Risk] Performance on large ranges (many DetalleVenta rows)** → Mitigation:
  queries are scoped by `empresa_id` + date range, and the existing indexes
  `ix_venta_empresa_id_fecha` and `detalle_venta(producto_id)` support the access
  paths; aggregation is in Python over the filtered set, same as C-18.
- **[Trade-off] No `/general` endpoint** → CA-4 served by C-18; one less surface
  to maintain, at the cost of the frontend calling two backends for the full
  view. Accepted per PO decision (2026-06-22).

## Migration Plan

- Additive only: new module + one `include_router` line in `main.py`. No schema
  migration, no data backfill.
- Rollback: remove the `include_router` line and the module directory; nothing
  else depends on it.

## Open Questions

- None blocking. (Possible future enhancement: expose the count of cortes
  excluded for `producto_id IS NULL`; not required by US-019.)
