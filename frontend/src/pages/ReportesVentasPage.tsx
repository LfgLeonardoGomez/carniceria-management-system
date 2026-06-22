/**
 * ReportesVentasPage — /reportes route.
 *
 * Composes ReportesFilters + ReportesTable.
 * Role guard: only administrador and encargado can access this page.
 * Unauthorized roles see "No autorizado" message.
 * TypeScript strict: no `any`.
 */
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { ReportesFilters } from '@/features/reportes/ReportesFilters'
import { ReportesTable } from '@/features/reportes/ReportesTable'
import { useReportesVentas } from '@/features/reportes/useReportesVentas'
import type { ReportesFilters as FiltersType } from '@/features/reportes/types'

const ALLOWED_ROLES = ['admin', 'administrador', 'encargado']

export function ReportesVentasPage() {
  const { user } = useAuthStore()
  const [filters, setFilters] = useState<FiltersType>({})

  // Role guard
  if (!user || !ALLOWED_ROLES.includes(user.rol)) {
    return (
      <div className="page-container">
        <p>No autorizado</p>
      </div>
    )
  }

  return <ReportesVentasContent filters={filters} onFilter={setFilters} />
}

function ReportesVentasContent({
  filters,
  onFilter,
}: {
  filters: FiltersType
  onFilter: (f: FiltersType) => void
}) {
  const { rows, total: _total, isLoading, error } = useReportesVentas(filters)

  return (
    <div className="page-container reportes-page">
      <h1>Reporte de ventas</h1>

      <ReportesFilters onFilter={onFilter} />

      {isLoading && <p className="loading-state">Cargando resultados...</p>}

      {!isLoading && error && (
        <p className="error-state">Error al cargar los reportes. Intentá de nuevo.</p>
      )}

      {!isLoading && !error && (
        <ReportesTable rows={rows} filters={filters} />
      )}
    </div>
  )
}
