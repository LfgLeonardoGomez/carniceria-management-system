# C-16 — Dashboard — Design

## Module structure

Nuevo módulo `backend/src/modules/dashboard/` (no toca `reporte`, que es de C-17):

```
dashboard/
├── __init__.py
├── router.py     # 3 endpoints, todos GET, todos Depends(get_current_user)
├── service.py    # funciones de agregación puras-ish (reciben db + empresa_id)
└── schemas.py    # response models Pydantic (BaseModel, extra='forbid')
```

**Sin `models.py`, sin migración**: el change es 100% solo-lectura. Agrega solo el seam de query sobre tablas existentes (`venta`, `detalle_venta`, `pago_venta`, `movimiento_stock`/`producto`, `gasto`).

## Endpoints y autorización

| Endpoint | Devuelve |
|----------|----------|
| `GET /dashboard/indicadores` | KPIs día/mes (ver spec) |
| `GET /dashboard/rankings` | productos más vendidos (top N, default 10) |
| `GET /dashboard/graficos` | series para charts |

**Autorización (decisión de diseño, least-privilege sobre US-004):**
- US-004 dice "cualquier usuario autenticado". Los KPIs **operativos** (ventas, kilos, clientes atendidos, stock crítico, productos más vendidos, distribución por medio de pago) se exponen a cualquier usuario autenticado, **scopeados a su `empresa_id`**.
- Los KPIs **financieros sensibles** (ganancia bruta/neta, costos) se gatean a `reportes:read` (hoy: admin/encargado). Un cajero/vendedor no ve la rentabilidad del negocio. Si el usuario no tiene `reportes:read`, esos campos vuelven `null` y el front no los renderiza.
- Rationale: mostrar márgenes/ganancia a todo el personal es una fuga de datos sensibles; el resto del termómetro operativo sí es para todos.

## Reglas de cálculo

- **Solo ventas `estado = 'cobrada'`** entran en ventas/kilos/ganancia/rankings/distribución. Se excluyen `en_curso`, `suspendida`, `anulada`.
- **Día** = `fecha >= inicio_del_dia_local` (timezone de la empresa, `config`); **mes** = desde el día 1. UTC en DB, conversión en el borde (regla dura del proyecto).
- **Dinero en `Decimal`**; kilos a 3 decimales.
- Toda query lleva `WHERE empresa_id = :empresa` (RN-SEG-01).

### KPIs (`/indicadores`)
- `ventas_dia` / `ventas_mes` = `SUM(venta.total)` cobradas en el rango.
- `kilos_vendidos` (mes) = `SUM(detalle_venta.cantidad_kilos)` de ventas cobradas.
- `clientes_atendidos` (día) = `COUNT(venta.id)` cobradas del día.
- `stock_critico` = `COUNT(producto)` con `activo AND stock_minimo IS NOT NULL AND stock_actual <= stock_minimo`.
- `gastos_mes` = `SUM(gasto.importe)` del mes.
- `ganancia_bruta` (mes) = `SUM(detalle.importe) − SUM(detalle.cantidad_kilos × detalle.costo_unitario)` — **DEPENDE del prereq `costo-snapshot-venta`**. Sin la columna `costo_unitario`, devolver `null` + flag `ganancia_disponible: false`.
- `ganancia_neta` (mes) = `ganancia_bruta − gastos_mes` (idem dependencia).

### Rankings (`/rankings`)
- `productos_mas_vendidos` = `GROUP BY detalle.producto_id ORDER BY SUM(cantidad_kilos) DESC LIMIT :top` sobre ventas cobradas. Devuelve `producto_id`, `nombre`, `kilos`.
- Cortes más vendidos: **fuera de v1.0** (no hay link `Producto`↔`TipoCorte`). Documentado, no se implementa.

### Gráficos (`/graficos`)
- `ventas_diarias` = `SUM(total) GROUP BY date(fecha)` últimos 7 días.
- `ventas_mensuales` = `SUM(total) GROUP BY year-month` últimos 12 meses.
- `distribucion_medio_pago` = `SUM(pago_venta.importe) GROUP BY medio_pago` (mes).
- `evolucion_ganancias` = serie mensual de `ganancia_bruta` — **depende del prereq**; sin snapshot, serie vacía + flag.

## Performance
- Agregación en vivo apoyada en los índices existentes (`empresa_id`, `fecha`, `cliente_id`, `estado`). Si más adelante pesa: caché corto por `(empresa_id, endpoint, día)` o migración a read-model (change futuro). No se optimiza prematuramente en v1.0.

## Frontend
- Pantalla `dashboard/` con KPI cards, charts (líneas: ventas diarias/mensuales/evolución; torta: distribución por medio; barras: ranking productos), tabla de rankings.
- Cards de ganancia ocultas si `ganancia_disponible: false` o el usuario no tiene `reportes:read`.
- React + TS estricto, Zustand para estado, React Query/SWR para server state, `Decimal` con librería de precisión.

## Testing (TDD)
- Backend: `pytest` + testcontainers (Postgres real). Unit para la lógica de agregación pura; integración para cada endpoint (cálculos, filtro por empresa, RBAC de ganancia, exclusión de no-cobradas).
- Frontend: Vitest + RTL para los componentes; sin Playwright (no es flujo crítico e2e).

## Out of scope / deferred
- Ganancia (hasta `costo-snapshot-venta`).
- Ranking de cortes (hasta link `Producto`↔`Corte`).
- Read-model / CQRS / caché (mitigación futura).
