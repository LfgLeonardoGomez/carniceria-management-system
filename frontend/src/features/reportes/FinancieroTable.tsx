/**
 * FinancieroTable — comparative table for the financial report.
 *
 * Shows one row per period with 5 indicators:
 *   ventas, costos, gastos, utilidad_bruta, utilidad_neta
 *
 * Null indicators (pre-snapshot historical cost) render as "no disponible"
 * and NEVER as "0". Money formatted with Decimal.js for precision.
 *
 * C-18, Task 8.2 GREEN. TypeScript strict: no `any`.
 */
import Decimal from 'decimal.js'
import type { FinancieroPeriodoRow } from './types'

// ---------------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------------

/** Format a Decimal-safe string for display. Uses Decimal.js to avoid float drift. */
function formatMoney(value: string): string {
  return new Decimal(value).toFixed(2)
}

/** Render a nullable indicator cell. */
function IndicatorCell({
  value,
  testId,
}: {
  value: string | null
  testId: string
}): JSX.Element {
  if (value === null) {
    return (
      <td data-testid={testId} className="financiero-cell null-indicator">
        no disponible
      </td>
    )
  }
  return (
    <td data-testid={testId} className="financiero-cell">
      {formatMoney(value)}
    </td>
  )
}

// ---------------------------------------------------------------------------
// FinancieroTable
// ---------------------------------------------------------------------------

interface FinancieroTableProps {
  rows: FinancieroPeriodoRow[]
}

export function FinancieroTable({ rows }: FinancieroTableProps): JSX.Element {
  if (rows.length === 0) {
    return (
      <p data-testid="financiero-empty" className="empty-state">
        Sin datos para el período seleccionado
      </p>
    )
  }

  return (
    <div className="financiero-table-wrapper">
      <table className="financiero-table">
        <thead>
          <tr>
            <th>Período</th>
            <th>Ventas</th>
            <th>Costos</th>
            <th>Gastos</th>
            <th>Utilidad bruta</th>
            <th>Utilidad neta</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.periodo} className="financiero-row">
              <td data-testid="financiero-periodo" className="financiero-cell">
                {row.periodo}
              </td>
              <td data-testid="financiero-ventas" className="financiero-cell">
                {formatMoney(row.ventas)}
              </td>
              <IndicatorCell value={row.costos} testId="financiero-costos" />
              <td data-testid="financiero-gastos" className="financiero-cell">
                {formatMoney(row.gastos)}
              </td>
              <IndicatorCell
                value={row.utilidad_bruta}
                testId="financiero-utilidad-bruta"
              />
              <IndicatorCell
                value={row.utilidad_neta}
                testId="financiero-utilidad-neta"
              />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
