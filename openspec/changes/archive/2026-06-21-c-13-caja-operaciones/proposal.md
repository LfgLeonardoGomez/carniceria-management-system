# Proposal — C-13 Caja Operaciones

## Why

BASILE needs cash-register (caja) lifecycle operations so a butcher shop can control
cash and other payment media per shift. Today the `Caja`/`MovimientoCaja` models exist
(migration 012, dragged in by C-12) and the venta service already requires an open caja
to cobrar non-cuenta_corriente sales, but there is **no endpoint to open, close, or move
money in a caja** — the `/caja` router is an empty stub. This blocks C-12 end-to-end:
without apertura, no efectivo/transferencia/tarjeta sale can ever be charged.

This change implements US-014 (Operar caja) and RN-CAJA-01..04:
- **RN-CAJA-01** apertura, cierre, movimientos.
- **RN-CAJA-02** at cierre, show diferencias between caja esperada (system-calculated) and
  caja real (manually entered). Flag significant differences.
- **RN-CAJA-03** control efectivo, transferencias and tarjetas (débito + crédito).
- **RN-CAJA-04** only Cajero/Encargado/Administrador operate caja (`caja:admin` permission).

## What changes

1. **Schema (migration 013, additive)** — extend the existing `caja` table with the cierre
   calculation columns the KB §Caja describes (`efectivo_esperado/real`,
   `transferencias_esperadas/reales`, `tarjetas_esperadas/reales`, per-medio + total
   `diferencia_*`, `usuario_cierre_id`). Add `descripcion` to `movimiento_caja`. All new
   columns nullable → does not break the 542-test baseline nor C-12.

2. **Endpoints** under `/caja` (router-by-domain):
   - `POST /caja/apertura` — open a caja with efectivo_inicial; reject if another caja is
     already `abierta` for the empresa (v1.0: one open caja per empresa).
   - `POST /caja/movimientos` — manual retiro / ingreso with descripción.
   - `POST /caja/cierre` — submit real counted amounts; compute esperado per medio,
     diferencias (real − esperado) and diferencia_total; flag significant difference;
     mark caja `cerrada`.
   - `GET /caja/actual` — read the currently open caja with live esperado (supports the
     close screen comparison).

3. **Service** (`caja/service.py`) — apertura uniqueness, esperado calculation from
   MovimientoCaja, diferencia computation, ACID transaction boundaries.

4. **Schemas** (`caja/schemas.py`) — Pydantic `extra='forbid'`, Decimal money.

5. **Frontend** — caja screen: apertura, movimientos, cierre with esperado-vs-real
   comparison.

## Out of scope / non-goals

- Notification on significant difference (RN-CAJA-02 step 11) — the `notificacion` module
  is a C-20 stub. This change **computes and returns** the difference flag and leaves a
  clear TODO seam for the future notification trigger; it does NOT depend on notificacion.
- Multi-caja per empresa (explicitly v1.0 = one open caja per empresa).
- Reversal of caja movements on venta anulación (already handled by C-12 venta service).

## Governance

ALTO (money). Non-obvious decisions (rounding, transaction boundaries, "significant"
difference threshold, additive migration vs. model recreation) are surfaced in design.md.
