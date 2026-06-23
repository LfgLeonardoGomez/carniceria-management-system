/**
 * RentabilidadFilters — shared date-range filter controls (Task 8.3).
 *
 * Used by both the productos and cortes tabs in RentabilidadPage.
 * Props are controlled — the parent owns the state.
 */
interface Props {
  fechaDesde: string | undefined
  fechaHasta: string | undefined
  onFechaDesdeChange: (value: string | undefined) => void
  onFechaHastaChange: (value: string | undefined) => void
}

export function RentabilidadFilters({
  fechaDesde,
  fechaHasta,
  onFechaDesdeChange,
  onFechaHastaChange,
}: Props) {
  return (
    <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
      <label>
        Desde
        <input
          type="date"
          data-testid="filter-fecha-desde"
          value={fechaDesde ?? ''}
          onChange={(e) =>
            onFechaDesdeChange(e.target.value === '' ? undefined : e.target.value)
          }
        />
      </label>
      <label>
        Hasta
        <input
          type="date"
          data-testid="filter-fecha-hasta"
          value={fechaHasta ?? ''}
          onChange={(e) =>
            onFechaHastaChange(e.target.value === '' ? undefined : e.target.value)
          }
        />
      </label>
    </div>
  )
}
