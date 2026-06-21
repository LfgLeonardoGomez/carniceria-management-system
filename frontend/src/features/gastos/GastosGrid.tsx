import { useState } from 'react'
import type { Gasto, CategoriaGasto } from '@/shared/types/gasto'
import { CATEGORIAS_GASTO, CATEGORIAS_GASTO_LABELS, MEDIOS_PAGO_GASTO_LABELS } from '@/shared/types/gasto'

interface GastosGridProps {
  gastos: Gasto[]
  total: number
  loading: boolean
  onEdit: (gasto: Gasto) => void
  onDelete: (gasto: Gasto) => void
  onFilter: (categoria: CategoriaGasto | undefined, fechaDesde: string, fechaHasta: string) => void
  categoriaActiva: CategoriaGasto | undefined
  fechaDesde: string
  fechaHasta: string
  canMutate: boolean
}

export function GastosGrid({
  gastos,
  total,
  loading,
  onEdit,
  onDelete,
  onFilter,
  categoriaActiva,
  fechaDesde,
  fechaHasta,
  canMutate,
}: GastosGridProps) {
  const [showConfirm, setShowConfirm] = useState<Gasto | null>(null)

  const handleConfirmDelete = () => {
    if (showConfirm) {
      onDelete(showConfirm)
      setShowConfirm(null)
    }
  }

  const handleCategoriaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    onFilter(
      val ? (val as CategoriaGasto) : undefined,
      fechaDesde,
      fechaHasta,
    )
  }

  const handleFechaDesdeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilter(categoriaActiva, e.target.value, fechaHasta)
  }

  const handleFechaHastaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilter(categoriaActiva, fechaDesde, e.target.value)
  }

  const formatImporte = (importe: string) => {
    const n = parseFloat(importe)
    return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(n)
  }

  return (
    <div className="gastos-grid">
      <div className="filters-bar">
        <select
          value={categoriaActiva ?? ''}
          onChange={handleCategoriaChange}
          disabled={loading}
          aria-label="Filtrar por categoría"
        >
          <option value="">Todas las categorías</option>
          {CATEGORIAS_GASTO.map((cat) => (
            <option key={cat} value={cat}>
              {CATEGORIAS_GASTO_LABELS[cat]}
            </option>
          ))}
        </select>

        <input
          type="date"
          value={fechaDesde}
          onChange={handleFechaDesdeChange}
          disabled={loading}
          aria-label="Fecha desde"
          placeholder="Fecha desde"
        />

        <input
          type="date"
          value={fechaHasta}
          onChange={handleFechaHastaChange}
          disabled={loading}
          aria-label="Fecha hasta"
          placeholder="Fecha hasta"
        />
      </div>

      <div className="total-info">Total: {total} gastos</div>

      {loading && <div className="loading">Cargando...</div>}

      <table className="gastos-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Categoría</th>
            <th>Descripción</th>
            <th>Importe</th>
            <th>Medio de pago</th>
            {canMutate && <th>Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {gastos.map((g) => (
            <tr key={g.id}>
              <td>{g.fecha}</td>
              <td>{CATEGORIAS_GASTO_LABELS[g.categoria]}</td>
              <td>{g.descripcion ?? '-'}</td>
              <td>{formatImporte(g.importe)}</td>
              <td>{MEDIOS_PAGO_GASTO_LABELS[g.medio_pago]}</td>
              {canMutate && (
                <td>
                  <button onClick={() => onEdit(g)} disabled={loading}>
                    Editar
                  </button>
                  <button
                    onClick={() => setShowConfirm(g)}
                    disabled={loading}
                    className="danger"
                  >
                    Eliminar
                  </button>
                </td>
              )}
            </tr>
          ))}
          {gastos.length === 0 && !loading && (
            <tr>
              <td colSpan={canMutate ? 6 : 5} className="empty">
                No hay gastos registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {showConfirm && (
        <div className="confirm-modal">
          <div className="confirm-content">
            <p>
              ¿Eliminar el gasto de{' '}
              <strong>{CATEGORIAS_GASTO_LABELS[showConfirm.categoria]}</strong> del{' '}
              <strong>{showConfirm.fecha}</strong>?
            </p>
            <div className="confirm-actions">
              <button onClick={() => setShowConfirm(null)}>Cancelar</button>
              <button onClick={handleConfirmDelete} className="danger">
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
