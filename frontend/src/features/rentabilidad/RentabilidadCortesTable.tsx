/**
 * RentabilidadCortesTable — cut margin view table (Task 8.2).
 *
 * Props:
 *   rows — from useRentabilidadCortes
 *
 * Null margin fields rendered as "no disponible".
 * costo_por_kilo is always present — never null.
 * Cuts with producto_id = NULL are excluded by the backend, never appear here.
 */
import type { CorteRentabilidadRow } from './types'

interface Props {
  rows: CorteRentabilidadRow[]
}

const NO_DISPONIBLE = 'no disponible'

function formatDecimal(value: string | null): string {
  if (value === null) return NO_DISPONIBLE
  return value
}

export function RentabilidadCortesTable({ rows }: Props) {
  return (
    <div>
      {rows.length === 0 ? (
        <div data-testid="rentabilidad-corte-empty">
          Sin cortes de desposte para el rango seleccionado.
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Tipo de corte</th>
              <th>Producto</th>
              <th>Costo/kg</th>
              <th>Precio venta prom.</th>
              <th>Margen %</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.tipo_corte}-${row.producto_id}`}>
                <td data-testid="rentabilidad-corte-tipo">{row.tipo_corte}</td>
                <td data-testid="rentabilidad-corte-producto">{row.nombre_producto}</td>
                <td data-testid="rentabilidad-corte-costo">{row.costo_por_kilo}</td>
                <td
                  data-testid="rentabilidad-corte-precio"
                  style={
                    row.precio_venta_promedio === null
                      ? { color: '#999', fontStyle: 'italic' }
                      : undefined
                  }
                >
                  {formatDecimal(row.precio_venta_promedio)}
                </td>
                <td
                  data-testid="rentabilidad-corte-margen"
                  style={
                    row.margen_porcentaje === null
                      ? { color: '#999', fontStyle: 'italic' }
                      : undefined
                  }
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
