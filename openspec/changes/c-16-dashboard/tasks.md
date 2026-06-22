# C-16 — Dashboard — Tasks

> TDD obligatorio: test antes del código para toda lógica de agregación. Backend con
> `pytest` + testcontainers (Postgres real). Solo lectura: sin modelos nuevos, sin migración.

## 1. Scaffolding del módulo
- [ ] 1.1 Crear `backend/src/modules/dashboard/{__init__.py,router.py,service.py,schemas.py}`.
- [ ] 1.2 Registrar el router en la app (`/dashboard`), con `Depends(get_current_user)`.
- [ ] 1.3 Definir schemas Pydantic (`IndicadoresResponse`, `RankingsResponse`, `GraficosResponse`) con `extra='forbid'` y campos `Decimal`.

## 2. Indicadores operativos (`GET /dashboard/indicadores`)
- [ ] 2.1 (RED) Test: `ventas_dia`/`ventas_mes` suman solo ventas `cobrada` en el rango; excluyen `en_curso`/`suspendida`/`anulada`.
- [ ] 2.2 (RED) Test: `kilos_vendidos` (mes) suma `cantidad_kilos` de ventas cobradas.
- [ ] 2.3 (RED) Test: `clientes_atendidos` cuenta ventas cobradas del día, incluido público general (sin `cliente_id`).
- [ ] 2.4 (RED) Test: `stock_critico` cuenta productos `activo` con `stock_minimo IS NOT NULL AND stock_actual <= stock_minimo`; ignora los sin umbral.
- [ ] 2.5 (RED) Test: `gastos_mes` suma `gasto.importe` del mes.
- [ ] 2.6 (RED) Test aislamiento: empresa A no ve datos de empresa B.
- [ ] 2.7 (GREEN) Implementar `service.calcular_indicadores(db, empresa_id, ahora_local)` + endpoint.
- [ ] 2.8 (REFACTOR) Extraer helpers de rango de fechas (día/mes con timezone de empresa).

## 3. Gating de ganancia (sensible + dependiente de prereq)
- [ ] 3.1 (RED) Test: usuario sin `reportes:read` (cajero/vendedor) recibe `ganancia_bruta`/`ganancia_neta` = `null`.
- [ ] 3.2 (RED) Test: sin `costo_unitario` en líneas (prereq pendiente) → ganancia `null` y `ganancia_disponible: false`.
- [ ] 3.3 (GREEN) Implementar el gate por permiso + detección de disponibilidad del snapshot.
- [ ] 3.4 (RED→GREEN) **[BLOQUEADO por `costo-snapshot-venta`]** Con snapshot disponible y `reportes:read`: `ganancia_bruta = Σ(importe) − Σ(cantidad_kilos × costo_unitario)`, `ganancia_neta = bruta − gastos_mes`.

## 4. Rankings (`GET /dashboard/rankings`)
- [ ] 4.1 (RED) Test: productos ordenados por `SUM(cantidad_kilos)` desc, top N (default 10), solo cobradas, con `producto_id/nombre/kilos`.
- [ ] 4.2 (GREEN) Implementar query + endpoint.
- [ ] 4.3 Nota: cortes más vendidos NO se implementa (diferido, sin link Producto↔Corte).

## 5. Gráficos (`GET /dashboard/graficos`)
- [ ] 5.1 (RED) Test: `ventas_diarias` agrupa por día (últimos 7), `ventas_mensuales` por mes (últimos 12).
- [ ] 5.2 (RED) Test: `distribucion_medio_pago` agrupa `SUM(importe)` por `medio_pago` del mes, solo cobradas.
- [ ] 5.3 (GREEN) Implementar series + endpoint. `evolucion_ganancias` dependiente del prereq (serie vacía + flag hasta entonces).

## 6. Frontend
- [ ] 6.1 Pantalla dashboard: KPI cards, charts (líneas/barras/torta), tabla de rankings.
- [ ] 6.2 Ocultar cards de ganancia si `ganancia_disponible: false` o sin `reportes:read`.
- [ ] 6.3 Tests Vitest + RTL de los componentes (render con datos, estados vacíos, ocultamiento de ganancia).

## 7. Cierre
- [ ] 7.1 Suite completa verde (backend + frontend).
- [ ] 7.2 Actualizar `CHANGES.md` C-16 a estado completado y marcar tareas dependientes del prereq que quedaron pendientes.
