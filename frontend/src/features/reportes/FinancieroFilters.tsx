/**
 * FinancieroFilters — group_by selector + date range filter for the financial report.
 *
 * C-18, Task 8.2 GREEN. TypeScript strict: no `any`.
 */
import { useState } from 'react'
import type { GroupBy, ReporteFinancieroFilters } from './types'

interface FinancieroFiltersProps {
  onFilter: (filters: ReporteFinancieroFilters) => void
}

export function FinancieroFilters({ onFilter }: FinancieroFiltersProps): JSX.Element {
  const [groupBy, setGroupBy] = useState<GroupBy>('mes')
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')

  const handleApply = () => {
    const filters: ReporteFinancieroFilters = { group_by: groupBy }
    if (fechaDesde) filters.fecha_desde = new Date(fechaDesde).toISOString()
    if (fechaHasta) filters.fecha_hasta = new Date(fechaHasta + 'T23:59:59').toISOString()
    onFilter(filters)
  }

  return (
    <div className="financiero-filters" data-testid="financiero-filters">
      <div className="filter-group">
        <label htmlFor="financiero-group-by">Agrupar por</label>
        <select
          id="financiero-group-by"
          data-testid="financiero-group-by"
          value={groupBy}
          onChange={(e) => setGroupBy(e.target.value as GroupBy)}
        >
          <option value="dia">Día</option>
          <option value="semana">Semana</option>
          <option value="mes">Mes</option>
          <option value="anio">Año</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="financiero-fecha-desde">Desde</label>
        <input
          id="financiero-fecha-desde"
          data-testid="financiero-fecha-desde"
          type="date"
          value={fechaDesde}
          onChange={(e) => setFechaDesde(e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label htmlFor="financiero-fecha-hasta">Hasta</label>
        <input
          id="financiero-fecha-hasta"
          data-testid="financiero-fecha-hasta"
          type="date"
          value={fechaHasta}
          onChange={(e) => setFechaHasta(e.target.value)}
        />
      </div>

      <button
        data-testid="financiero-apply-filters"
        onClick={handleApply}
        type="button"
      >
        Aplicar
      </button>
    </div>
  )
}
