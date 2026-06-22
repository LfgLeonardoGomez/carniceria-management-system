# Design — C-13 Caja Operaciones

## Context

- Models `Caja` / `MovimientoCaja` already exist (`backend/src/modules/caja/models.py`,
  migration 012). The existing `Caja` has `monto_inicial`, `monto_final`, `operador_id`,
  `fecha_apertura`, `fecha_cierre`, `estado`. `MovimientoCaja` has `tipo`, `medio`,
  `importe`, `venta_id`, `fecha`.
- The venta service writes `MovimientoCaja(tipo="entrada_venta", medio=<medio_pago>, importe=total)`
  on cobro, and reversal rows `tipo="salida_anulacion"` on anulación. **The cierre esperado
  must be derived from these rows** — this is the integration contract with C-12.
- RBAC: `caja:admin` permission (admin + cajero have it; encargado does NOT in the current
  matrix — see Decision 5).

## Decisions

### D1 — Additive migration 013, do NOT recreate the model
The KB §Caja describes richer columns than the existing table. Recreating the table or the
SQLModel would break C-12 (which sets `monto_inicial` and reads `estado`) and the 542
baseline. Instead, migration 013 **adds nullable columns** to `caja`
(`efectivo_esperado`, `efectivo_real`, `transferencias_esperadas`, `transferencias_reales`,
`tarjetas_esperadas`, `tarjetas_reales`, `diferencia_efectivo`, `diferencia_transferencias`,
`diferencia_tarjetas`, `diferencia_total`, `usuario_cierre_id`) and `descripcion` to
`movimiento_caja`. `monto_inicial` remains the canonical efectivo_inicial; the apertura
endpoint writes `monto_inicial = efectivo_inicial`. `monto_final` is set at cierre to the
sum of real medios for backward compat.

### D2 — Esperado calculation (RN-CAJA-03)
From `MovimientoCaja` rows of the open caja:
- `ventas_efectivo`   = Σ importe where tipo in (entrada_venta, salida_anulacion) and medio == efectivo
- `ventas_transferencia` = same, medio == transferencia
- `ventas_debito` / `ventas_credito` = same, medio in (debito / credito)
- `ingresos_manuales` = Σ importe where tipo == ingreso_manual
- `retiros`           = Σ importe where tipo == retiro   (stored as positive magnitude)

Then:
- `efectivo_esperado`        = monto_inicial + ventas_efectivo + ingresos_manuales − retiros
- `transferencias_esperadas` = ventas_transferencia
- `tarjetas_esperadas`       = ventas_debito + ventas_credito

Note: `salida_anulacion` importe is stored **negative** by the venta service, so summing it
naturally subtracts reversed sales. Retiros are stored as **positive** magnitude and
subtracted explicitly; ingresos_manuales positive and added.

### D3 — Diferencias (RN-CAJA-02)
`diferencia_<medio> = real_<medio> − esperado_<medio>` for each of the three media.
`diferencia_total = Σ diferencias`. A positive diff = sobrante, negative = faltante.

### D4 — "Significant" difference threshold + notification seam
`tiene_diferencia = diferencia_total != 0`.
`diferencia_significativa = abs(diferencia_total) >= UMBRAL_DIFERENCIA_SIGNIFICATIVA`
where `UMBRAL_DIFERENCIA_SIGNIFICATIVA = Decimal("0.01")` (any real discrepancy is
significant for v1.0; constant is centralized so C-20 / config can tune it). The cierre
response returns both flags. A `# TODO(C-20)` seam marks where the notificacion trigger
will fire — this change does NOT import or call notificacion.

### D5 — RBAC: reuse `caja:admin`
The existing matrix grants `caja:admin` to admin + cajero. RN-CAJA-04 also names Encargado,
but the current PERMISSION_MATRIX does NOT give encargado `caja:admin`. Changing the matrix
is a CRITICAL (security) edit out of this change's scope — **I will NOT modify RBAC here**.
All caja endpoints require `caja:admin`. If the business wants encargado to operate caja,
that is a separate RBAC change. This is surfaced as a known gap.

### D6 — Money & rounding
All amounts `Decimal`, quantized to `Decimal("0.01")` (centavos). NEVER float. Inputs
validated in Pydantic (`ge=0`, `decimal_places=2`, `max_digits=19`, `extra='forbid'`).

### D7 — ACID transaction boundaries
Apertura, cierre and each movimiento are single atomic commits. Apertura uniqueness is
enforced by querying for an existing `abierta` caja inside the same request before insert
(advisory; a partial-unique DB index `WHERE estado='abierta'` is a future hardening, noted
but not added in v1.0 to keep the migration minimal and reversible).

### D8 — Multi-tenant
Every query filters `empresa_id = current_user.empresa_id`. Apertura/cierre/movimiento all
scope to the caller's empresa. Cross-tenant caja access returns 404.

## Risks

- **R1 (medium)**: encargado cannot operate caja under current RBAC (D5). Mitigation:
  documented gap; behavior matches existing matrix, no silent privilege change.
- **R2 (low)**: no DB-level partial-unique index on open caja (D7). Mitigation: service-level
  check; single-writer butcher-shop workload makes the race negligible in v1.0.
