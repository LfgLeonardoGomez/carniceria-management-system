# C-16 — Dashboard de indicadores

## Why

Un usuario autenticado (US-004) necesita una vista de un vistazo del estado del negocio: cuánto se vendió hoy y en el mes, kilos movidos, ganancia, gastos, stock crítico y rankings. Hoy esos datos están dispersos en ventas, stock, gastos y desposte, sin ninguna agregación. Sin dashboard, el dueño no tiene termómetro diario y tiene que entrar módulo por módulo.

Es el primer change de FASE 6 y se habilita recién ahora: depende de C-09 (desposte), C-12 (ventas), C-13 (caja) y C-15 (gastos), todos completos (GATE 6 ✓).

## What Changes

- **`GET /dashboard/indicadores`** — KPIs del día y del mes, filtrados por `empresa_id` del usuario:
  - Ventas del día, ventas del mes, kilos vendidos, clientes atendidos.
  - Ganancia bruta (ventas − costo), ganancia neta (bruta − gastos del mes), gastos del mes.
  - Stock crítico: cantidad de productos por debajo de su umbral.
- **`GET /dashboard/rankings`** — productos más vendidos y cortes más vendidos (top N).
- **`GET /dashboard/graficos`** — series para los gráficos: ventas diarias (últimos 7 días), ventas mensuales (últimos 12 meses), evolución de ganancias, distribución de ventas por medio de pago.
- **Frontend**: pantalla principal con KPI cards, gráficos (líneas/barras/torta) y tabla de rankings.

## Approach

- **Agregación en vivo** (decisión de producto, este change): cada request agrega directo sobre las tablas reales (`venta`, `detalle_venta`, `pago_venta`, `movimiento_stock`, `gasto`, `corte_desposte`) con SQL + índices. Exacto siempre, sin tablas precomputadas ni jobs de sincronización. Si el volumen escala, se migra a read-model en un change futuro — los cálculos quedan validados por estos tests.
- **Solo lectura**: ningún endpoint muta estado. Toda query lleva `WHERE empresa_id = :empresa` (aislamiento multi-tenant, RN-SEG-01).
- **Solo ventas `cobrada`** cuentan para ventas/ganancia; las `anulada`/`en_curso`/`suspendida` se excluyen.
- **Dinero en `Decimal`**, kilos con 3 decimales (reglas duras del proyecto).

## Out of scope

- Read-model / CQRS / vistas materializadas (diferido; ver decisión).
- Reportes exportables con filtros por rango/cliente → es **C-17 reportes-ventas**.
- Caché de respuestas (mitigación futura si la agregación en vivo pesa).

## Decisiones (resueltas)

1. **Stock crítico**: count de productos con `stock_actual <= stock_minimo` (campo real `Producto.stock_minimo`, `Decimal` nullable), `stock_minimo IS NOT NULL AND activo`. Productos sin umbral no cuentan.
2. **Cortes más vendidos**: **DIFERIDO** de v1.0. No existe link `Producto`↔`TipoCorte`/`CorteDesposte` en el modelo, así que "cortes más vendidos por venta" no es calculable hoy. El dashboard muestra solo **productos más vendidos** (`DetalleVenta` → `Producto`, por kilos). El ranking de cortes se retoma cuando exista ese link (US-004 CA-2 queda parcial, documentado).
3. **Clientes atendidos**: count de ventas `cobrada` del día (cada venta = un cliente atendido, incluido el público general de mostrador; `distinct cliente_id` dejaría afuera al mostrador y sería engañoso).

## Dependencia

- **Ganancia bruta/neta** depende del prerequisito **`costo-snapshot-venta`** (amend C-12): sin el snapshot de `costo_unitario` en `DetalleVenta`, la ganancia histórica no es correcta. Hasta que ese prereq esté, los KPIs de ganancia quedan marcados como pendientes; el resto del dashboard no se bloquea. Ver `CHANGES.md` §FASE 6 y engram `basile/costo-snapshot-venta`.
