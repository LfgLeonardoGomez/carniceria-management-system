# Dashboard — Delta Spec (C-16)

## ADDED Requirements

### Requirement: Indicadores clave del negocio
El sistema SHALL exponer `GET /dashboard/indicadores` con KPIs operativos y financieros del día y del mes, calculados en vivo y scopeados a la `empresa_id` del usuario autenticado.

#### Scenario: KPIs operativos del día y del mes
- **WHEN** un usuario autenticado pide `/dashboard/indicadores`
- **THEN** recibe `ventas_dia`, `ventas_mes`, `kilos_vendidos`, `clientes_atendidos`, `gastos_mes` y `stock_critico`
- **AND** todos los montos están en `Decimal` y solo consideran ventas en estado `cobrada`

#### Scenario: Stock crítico
- **WHEN** se calcula `stock_critico`
- **THEN** cuenta los productos `activo` con `stock_minimo IS NOT NULL AND stock_actual <= stock_minimo`
- **AND** los productos sin `stock_minimo` definido no se cuentan

#### Scenario: Clientes atendidos incluye público general
- **WHEN** se calcula `clientes_atendidos` del día
- **THEN** cuenta las ventas `cobrada` del día (cada venta = un cliente atendido)
- **AND** las ventas sin `cliente_id` (público general) se cuentan igual

#### Scenario: Aislamiento por empresa
- **WHEN** un usuario de la empresa A pide indicadores
- **THEN** los cálculos solo incluyen datos de la empresa A
- **AND** ningún dato de otra empresa aparece en el resultado

### Requirement: Gating de KPIs financieros sensibles
El sistema SHALL exponer los KPIs de ganancia (bruta y neta) solo a usuarios con permiso `reportes:read`; al resto les devuelve esos campos en `null`.

#### Scenario: Usuario con reportes:read ve ganancia
- **WHEN** un admin o encargado pide indicadores
- **AND** el snapshot de costo está disponible
- **THEN** `ganancia_bruta` y `ganancia_neta` traen valores `Decimal`

#### Scenario: Usuario sin reportes:read no ve ganancia
- **WHEN** un cajero o vendedor pide indicadores
- **THEN** `ganancia_bruta` y `ganancia_neta` vienen `null`

#### Scenario: Ganancia no disponible sin snapshot de costo
- **WHEN** las líneas de venta no tienen `costo_unitario` persistido (prereq `costo-snapshot-venta` pendiente)
- **THEN** `ganancia_bruta`/`ganancia_neta` vienen `null`
- **AND** el resultado incluye `ganancia_disponible: false`

### Requirement: Ranking de productos más vendidos
El sistema SHALL exponer `GET /dashboard/rankings` con los productos más vendidos por kilos, top N (default 10), sobre ventas `cobrada` de la empresa.

#### Scenario: Top productos por kilos
- **WHEN** un usuario autenticado pide `/dashboard/rankings`
- **THEN** recibe los productos ordenados por `SUM(cantidad_kilos)` descendente
- **AND** cada item trae `producto_id`, `nombre` y `kilos`

### Requirement: Series para gráficos
El sistema SHALL exponer `GET /dashboard/graficos` con las series de ventas diarias (7 días), ventas mensuales (12 meses) y distribución por medio de pago del mes, scopeadas por empresa.

#### Scenario: Distribución por medio de pago
- **WHEN** un usuario pide `/dashboard/graficos`
- **THEN** `distribucion_medio_pago` agrupa `SUM(importe)` por `medio_pago` del mes
- **AND** solo incluye pagos de ventas `cobrada` de la empresa
