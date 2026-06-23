/**
 * HistorialCCTable — renders the movement history table (C-14, Task 6.4).
 *
 * Props:
 *   items     — movement list from HistorialCCResponse
 *   saldo     — current saldo_actual string
 *
 * TypeScript strict: no `any`.
 */
import type { MovimientoCC } from './types'

interface HistorialCCTableProps {
  items: MovimientoCC[]
  saldo: string
}

export function HistorialCCTable({ items, saldo }: HistorialCCTableProps): JSX.Element {
  return (
    <div data-testid="historial-cc-table">
      <p data-testid="historial-saldo-actual">
        Saldo actual: <strong>{saldo}</strong>
      </p>
      {items.length === 0 ? (
        <p data-testid="historial-empty">Sin movimientos registrados.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Tipo</th>
              <th>Importe</th>
              <th>Saldo resultante</th>
              <th>Venta</th>
            </tr>
          </thead>
          <tbody>
            {items.map((mov) => (
              <tr key={mov.id} data-testid={`mov-row-${mov.id}`}>
                <td>{new Date(mov.fecha).toLocaleString('es-AR')}</td>
                <td>{mov.tipo}</td>
                <td style={{ textAlign: 'right' }}>{mov.importe}</td>
                <td style={{ textAlign: 'right' }}>{mov.saldo_resultante}</td>
                <td>{mov.venta_id ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
