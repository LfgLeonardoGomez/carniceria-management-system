/**
 * FinancieroChart — comparative bar chart for the financial report.
 *
 * Implements a pure-CSS bar chart (no external charting library).
 * The C-16 dashboard also uses no charting library (verified at apply).
 * Reusing the same no-dep pattern keeps the bundle unchanged.
 *
 * Each period shows bars for ventas, costos (if available), and gastos.
 * Null costos are rendered as a "N/A" placeholder bar.
 *
 * C-18, Task 8.4 GREEN. TypeScript strict: no `any`.
 */
import Decimal from 'decimal.js'
import type { FinancieroPeriodoRow } from './types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toFloat(value: string | null, fallback = 0): number {
  if (value === null) return fallback
  return new Decimal(value).toNumber()
}

// ---------------------------------------------------------------------------
// FinancieroChart
// ---------------------------------------------------------------------------

interface FinancieroChartProps {
  rows: FinancieroPeriodoRow[]
}

export function FinancieroChart({ rows }: FinancieroChartProps): JSX.Element {
  if (rows.length === 0) {
    return (
      <p data-testid="chart-empty" className="empty-state">
        Sin datos para graficar
      </p>
    )
  }

  // Compute max value for scaling bars (include all numeric indicators)
  const maxValue = Math.max(
    ...rows.flatMap((row) => [
      toFloat(row.ventas),
      toFloat(row.costos),
      toFloat(row.gastos),
      toFloat(row.utilidad_bruta),
      toFloat(row.utilidad_neta),
    ]),
    1,  // floor to prevent div-by-zero
  )

  const barHeight = (value: number): string =>
    `${Math.max((value / maxValue) * 100, 0).toFixed(1)}%`

  return (
    <div data-testid="financiero-chart" className="financiero-chart">
      <div className="chart-legend">
        <span className="legend-ventas">Ventas</span>
        <span className="legend-costos">Costos</span>
        <span className="legend-gastos">Gastos</span>
      </div>
      <div className="chart-bars-wrapper">
        {rows.map((row) => {
          const ventasH = barHeight(toFloat(row.ventas))
          const costosH = row.costos !== null ? barHeight(toFloat(row.costos)) : null
          const gastosH = barHeight(toFloat(row.gastos))

          return (
            <div
              key={row.periodo}
              data-testid="chart-bar-group"
              className="chart-bar-group"
            >
              {/* Ventas bar */}
              <div
                className="chart-bar bar-ventas"
                style={{ height: ventasH }}
                title={`Ventas: ${row.ventas}`}
              />
              {/* Costos bar or N/A placeholder */}
              {costosH !== null ? (
                <div
                  className="chart-bar bar-costos"
                  style={{ height: costosH }}
                  title={`Costos: ${row.costos}`}
                />
              ) : (
                <div
                  className="chart-bar bar-costos-na"
                  style={{ height: '4px' }}
                  title="Costos: no disponible"
                />
              )}
              {/* Gastos bar */}
              <div
                className="chart-bar bar-gastos"
                style={{ height: gastosH }}
                title={`Gastos: ${row.gastos}`}
              />
              <span className="chart-label">{row.periodo}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
