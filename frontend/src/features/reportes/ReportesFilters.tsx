/**
 * ReportesFilters — filter panel for the sales report page.
 *
 * Controls:
 * - Date range pickers (fecha_desde / fecha_hasta)
 * - Cliente dropdown (fetched from empresa's client list)
 * - Apply button that calls onFilter with the current filter state
 *
 * Empty date values are passed as undefined (not empty string).
 * TypeScript strict: no `any`.
 */
import { useEffect, useState } from 'react'
import { fetchClientes } from '@/features/clientes/api'
import type { Cliente } from '@/shared/types/cliente'
import type { ReportesFilters } from './types'

interface ReportesFiltersProps {
  onFilter: (filters: ReportesFilters) => void
}

export function ReportesFilters({ onFilter }: ReportesFiltersProps) {
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [clienteId, setClienteId] = useState<string>('')
  const [clientes, setClientes] = useState<Cliente[]>([])

  useEffect(() => {
    fetchClientes({ limit: 500 })
      .then((res) => setClientes(res.items ?? []))
      .catch(() => setClientes([]))
  }, [])

  function handleApply() {
    const filters: ReportesFilters = {}
    if (fechaDesde) filters.fecha_desde = new Date(fechaDesde).toISOString()
    if (fechaHasta) {
      // Set to end of day for the hasta date
      const d = new Date(fechaHasta)
      d.setHours(23, 59, 59, 999)
      filters.fecha_hasta = d.toISOString()
    }
    if (clienteId) filters.cliente_id = clienteId
    onFilter(filters)
  }

  return (
    <div className="reportes-filters">
      <div className="filter-row">
        <label htmlFor="fecha-desde">Fecha desde</label>
        <input
          id="fecha-desde"
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
        />
      </div>

      <div className="filter-row">
        <label htmlFor="fecha-hasta">Fecha hasta</label>
        <input
          id="fecha-hasta"
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
        />
      </div>

      <div className="filter-row">
        <label htmlFor="cliente-select">Cliente</label>
        <select
          id="cliente-select"
          aria-label="Cliente"
          value={clienteId}
          onChange={(e) => setClienteId(e.target.value)}
        >
          <option value="">Todos los clientes</option>
          {clientes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.razon_social ?? `${c.nombre}${c.apellido ? ' ' + c.apellido : ''}`}
            </option>
          ))}
        </select>
      </div>

      <button type="button" onClick={handleApply}>
        Aplicar filtros
      </button>
    </div>
  )
}
