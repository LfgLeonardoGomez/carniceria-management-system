/**
 * RentabilidadProductosTable — product profitability ranking table (Task 8.1).
 *
 * Props:
 *   rows          — from useRentabilidadProductos
 *   orden         — current sort direction ("mayor" | "menor")
 *   onOrdenChange — called when the toggle changes
 *   top           — optional Top-N control value
 *   onTopChange   — optional Top-N change handler
 *
 * Null margin is rendered as "no disponible" with a distinct style.
 * Never renders null as "0.00" or "0%".
 */
import type { ProductoRentabilidadRow, OrdenRentabilidad } from './types'

interface Props {
  rows: ProductoRentabilidadRow[]
  orden: OrdenRentabilidad
  onOrdenChange: (orden: OrdenRentabilidad) => void
  top?: number
  onTopChange?: (top: number | undefined) => void
}

const NO_DISPONIBLE = 'no disponible'

function formatDecimal(value: string | null): string {
  if (value === null) return NO_DISPONIBLE
  return value
}

export function RentabilidadProductosTable({
  rows,
  orden,
  onOrdenChange,
  top,
  onTopChange,
}: Props) {
  return (
    <div>
      {/* Toggle most / least profitable */}
      <div style={{ marginBottom: 8 }}>
        <button
          data-testid="toggle-orden-mayor"
          onClick={() => onOrdenChange('mayor')}
          aria-pressed={orden === 'mayor'}
        >
          Más rentable
        </button>
        <button
          data-testid="toggle-orden-menor"
          onClick={() => onOrdenChange('menor')}
          aria-pressed={orden === 'menor'}
        >
          Menos rentable
        </button>

        {onTopChange && (
          <select
            data-testid="top-n-select"
            value={top ?? ''}
            onChange={(e) => {
              const v = e.target.value
              onTopChange(v === '' ? undefined : Number(v))
            }}
          >
            <option value="">Todos</option>
            <option value="5">Top 5</option>
            <option value="10">Top 10</option>
            <option value="20">Top 20</option>
          </select>
        )}
      </div>

      {rows.length === 0 ? (
        <div data-testid="rentabilidad-prod-empty">
          Sin datos de rentabilidad para el rango seleccionado.
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Ventas</th>
              <th>Ganancia</th>
              <th>Margen %</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.producto_id}>
                <td data-testid="rentabilidad-prod-nombre">{row.nombre}</td>
                <td data-testid="rentabilidad-prod-ventas">{row.ventas}</td>
                <td
                  data-testid="rentabilidad-prod-ganancia"
                  style={row.ganancia === null ? { color: '#999', fontStyle: 'italic' } : undefined}
                >
                  {formatDecimal(row.ganancia)}
                </td>
                <td
                  data-testid="rentabilidad-prod-margen"
                  style={row.margen_porcentaje === null ? { color: '#999', fontStyle: 'italic' } : undefined}
                >
                  {formatDecimal(row.margen_porcentaje)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
