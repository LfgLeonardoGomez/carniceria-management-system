/**
 * ReportesFinancierosPage — /reportes/financieros route.
 *
 * Composes FinancieroFilters + FinancieroChart + FinancieroTable.
 * Role guard: only administrador and encargado can access this page.
 * Unauthorized roles see "No autorizado" message.
 *
 * C-18, Task 8.4 + 8.5 GREEN. TypeScript strict: no `any`.
 */
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { FinancieroFilters } from '@/features/reportes/FinancieroFilters'
import { FinancieroChart } from '@/features/reportes/FinancieroChart'
import { FinancieroTable } from '@/features/reportes/FinancieroTable'
import { useReporteFinanciero } from '@/features/reportes/useReporteFinanciero'
import type { ReporteFinancieroFilters } from '@/features/reportes/types'

const ALLOWED_ROLES = ['admin', 'administrador', 'encargado']

export function ReportesFinancierosPage(): JSX.Element {
  const { user } = useAuthStore()
  const [filters, setFilters] = useState<ReporteFinancieroFilters>({ group_by: 'mes' })

  // Role guard
  if (!user || !ALLOWED_ROLES.includes(user.rol)) {
    return (
      <div className="page-container" data-testid="reportes-financieros-unauthorized">
        <p>No autorizado</p>
      </div>
    )
  }

  return (
    <ReportesFinancierosContent filters={filters} onFilter={setFilters} />
  )
}

function ReportesFinancierosContent({
  filters,
  onFilter,
}: {
  filters: ReporteFinancieroFilters
  onFilter: (f: ReporteFinancieroFilters) => void
}): JSX.Element {
  const { rows, isLoading, error } = useReporteFinanciero(filters)

  return (
    <div className="page-container reportes-financieros-page" data-testid="reportes-financieros-page">
      <h1>Reporte financiero</h1>

      <FinancieroFilters onFilter={onFilter} />

      {isLoading && (
        <p className="loading-state" data-testid="reportes-financieros-loading">
          Cargando datos financieros...
        </p>
      )}

      {!isLoading && error && (
        <p className="error-state" data-testid="reportes-financieros-error">
          Error al cargar los datos. Intentá de nuevo.
        </p>
      )}

      {!isLoading && !error && (
        <>
          <section className="financiero-chart-section">
            <h2>Comparativa por período</h2>
            <FinancieroChart rows={rows} />
          </section>

          <section className="financiero-table-section">
            <h2>Detalle por período</h2>
            <FinancieroTable rows={rows} />
          </section>
        </>
      )}
    </div>
  )
}
