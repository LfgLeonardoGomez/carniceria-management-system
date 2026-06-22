# Tasks — C-13 Caja Operaciones

## 1. Schema (migration 013, additive)
- [x] 1.1 Extend `Caja` SQLModel with nullable cierre columns + `usuario_cierre_id`
- [x] 1.2 Add `descripcion` nullable column to `MovimientoCaja` SQLModel
- [x] 1.3 Write migration `000000000013_extend_caja_cierre_columns.py` (upgrade + downgrade)
- [x] 1.4 Verify migration applies on real PostgreSQL (test)

## 2. Schemas (Pydantic, extra='forbid', Decimal)
- [x] 2.1 `AperturaCajaRequest`, `CajaRead`
- [x] 2.2 `MovimientoCajaRequest`, `MovimientoCajaRead`
- [x] 2.3 `CierreCajaRequest`, `CierreCajaResponse` (with esperado, real, diferencias, flags)
- [x] 2.4 `CajaEsperadoRead` (live esperado for the close screen)

## 3. Service (caja/service.py)
- [x] 3.1 `abrir_caja` — uniqueness check (one abierta per empresa) + ACID
- [x] 3.2 `registrar_movimiento` — retiro / ingreso_manual against open caja
- [x] 3.3 `_calcular_esperado` — pure-ish esperado per medio from MovimientoCaja
- [x] 3.4 `cerrar_caja` — compute diferencias, flags, set estado=cerrada, ACID
- [x] 3.5 `obtener_caja_abierta_con_esperado` — for GET /caja/actual

## 4. Router (caja/router.py) + register
- [x] 4.1 `POST /caja/apertura` (caja:admin)
- [x] 4.2 `POST /caja/movimientos` (caja:admin)
- [x] 4.3 `POST /caja/cierre` (caja:admin)
- [x] 4.4 `GET /caja/actual` (caja:admin)
- [x] 4.5 Confirm router registered in main.py (already imported at line 84/103)

## 5. Tests (TDD — RED first, real PostgreSQL)
- [x] 5.1 Unit: `_calcular_esperado` (efectivo formula, tarjetas débito+crédito, diferencias)
- [x] 5.2 Integration: apertura única (happy + second apertura → 409)
- [x] 5.3 Integration: movimientos retiro/ingreso (happy + no-caja → 409)
- [x] 5.4 Integration: cierre esperado-vs-real + diferencias + flag (sin diff, con faltante)
- [x] 5.5 Integration: multi-tenant isolation
- [x] 5.6 Integration: RBAC 403 for rol without caja:admin

## 6. Frontend (caja screen)
- [x] 6.1 API client functions (apertura, movimientos, cierre, actual)
- [x] 6.2 Caja apertura + movimientos + cierre screen with esperado-vs-real comparison
- [x] 6.3 Frontend test (Vitest) for the comparison/diferencia logic

## 7. Safety net
- [x] 7.1 Full backend suite green; 542 baseline not regressed (559 passed; 22 new caja tests; 0 C-13 regressions — see note below)
