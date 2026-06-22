/**
 * ReportesTable — results table for the sales report.
 *
 * Columns: fecha, cliente, productos, kilos, subtotal, total, medio_pago, ganancia_estimada
 * null ganancia → '—' (em-dash)
 * Empty state: "Sin resultados" message
 * Export buttons: disabled when rows is empty; trigger file download via buildExportUrl
 * TypeScript strict: no `any`.
 */
import { buildExportUrl } from './api'
import type { VentaReporteRow, ReportesFilters, ExportFormato } from './types'

interface ReportesTableProps {
  rows: VentaReporteRow[]
  filters: ReportesFilters
}

/**
 * Build the download filename with the applied date range.
 *
 * Rules (mirrors backend _build_filename):
 *   both dates present  → ventas-<desde_date>-<hasta_date>.<fmt>
 *   both dates absent   → ventas.<fmt>
 *   only desde present  → ventas-<desde_date>-all.<fmt>
 *   only hasta present  → ventas-all-<hasta_date>.<fmt>
 *
 * Date portion extracted as the first 10 chars of the ISO-8601 string (YYYY-MM-DD).
 */
export function buildDownloadFilename(formato: ExportFormato, filters: ReportesFilters): string {
  const { fecha_desde, fecha_hasta } = filters
  if (!fecha_desde && !fecha_hasta) {
    return `ventas.${formato}`
  }
  const desdeStr = fecha_desde ? fecha_desde.slice(0, 10) : 'all'
  const hastaStr = fecha_hasta ? fecha_hasta.slice(0, 10) : 'all'
  return `ventas-${desdeStr}-${hastaStr}.${formato}`
}

export function ReportesTable({ rows, filters }: ReportesTableProps) {
  const hasRows = rows.length > 0

  function handleExport(formato: ExportFormato) {
    if (!hasRows) return
    const url = buildExportUrl(formato, filters)
    const a = document.createElement('a')
    a.href = url
    const token = localStorage.getItem('access_token')
    if (token) a.setAttribute('data-token', token)
    a.download = buildDownloadFilename(formato, filters)
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  return (
    <div className="reportes-table-container">
      <div className="export-buttons">
        <button
          type="button"
          onClick={() => handleExport('xlsx')}
          disabled={!hasRows}
        >
          Export Excel
        </button>
        <button
          type="button"
          onClick={() => handleExport('pdf')}
          disabled={!hasRows}
        >
          Export PDF
        </button>
        <button
          type="button"
          onClick={() => handleExport('csv')}
          disabled={!hasRows}
        >
          Export CSV
        </button>
      </div>

      {!hasRows ? (
        <p className="empty-state">Sin resultados</p>
      ) : (
        <table className="reportes-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Cliente</th>
              <th>Productos</th>
              <th>Kilos</th>
              <th>Subtotal</th>
              <th>Total</th>
              <th>Medio de pago</th>
              <th>Ganancia est.</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.venta_id}>
                <td>{new Date(row.fecha).toLocaleDateString('es-AR')}</td>
                <td>{row.cliente_nombre}</td>
                <td>{row.productos}</td>
                <td>{row.total_kilos}</td>
                <td>{row.subtotal}</td>
                <td>{row.total}</td>
                <td>{row.medios_pago}</td>
                <td>{row.ganancia_estimada !== null ? row.ganancia_estimada : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
