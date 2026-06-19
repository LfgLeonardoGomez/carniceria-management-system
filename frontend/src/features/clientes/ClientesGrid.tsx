import { useState } from 'react'
import type { Cliente } from '@/shared/types/cliente'

interface ClientesGridProps {
  clientes: Cliente[]
  total: number
  loading: boolean
  onEdit: (cliente: Cliente) => void
  onDelete: (cliente: Cliente) => void
  onSearch: (q: string) => void
  onFilterTipo: (tipo: string) => void
  onNavigate: (cliente: Cliente) => void
  search: string
  tipoFilter: string
  canMutate: boolean
}

const TIPOS_CLIENTE = [
  { value: '', label: 'Todos' },
  { value: 'publico_general', label: 'Público General' },
  { value: 'mayorista', label: 'Mayorista' },
  { value: 'especial', label: 'Especial' },
]

export function ClientesGrid({
  clientes,
  total,
  loading,
  onEdit,
  onDelete,
  onSearch,
  onFilterTipo,
  onNavigate,
  search,
  tipoFilter,
  canMutate,
}: ClientesGridProps) {
  const [showConfirm, setShowConfirm] = useState<Cliente | null>(null)

  const handleConfirmDelete = () => {
    if (showConfirm) {
      onDelete(showConfirm)
      setShowConfirm(null)
    }
  }

  return (
    <div className="clientes-grid">
      <div className="filters-bar">
        <input
          type="text"
          placeholder="Buscar por nombre, CUIT..."
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          disabled={loading}
        />
        <select
          value={tipoFilter}
          onChange={(e) => onFilterTipo(e.target.value)}
          disabled={loading}
        >
          {TIPOS_CLIENTE.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </div>

      <div className="total-info">Total: {total} clientes</div>

      {loading && <div className="loading">Cargando...</div>}

      <table className="clientes-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Apellido</th>
            <th>CUIT</th>
            <th>Tipo</th>
            <th>Saldo</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {clientes.map((c) => (
            <tr
              key={c.id}
              className={c.activo ? '' : 'inactive'}
              onClick={() => onNavigate(c)}
              style={{ cursor: 'pointer' }}
            >
              <td>{c.nombre}</td>
              <td>{c.apellido || '-'}</td>
              <td>{c.cuit || '-'}</td>
              <td>{c.tipo_cliente}</td>
              <td>{c.saldo_actual}</td>
              <td>{c.activo ? 'Activo' : 'Inactivo'}</td>
              <td onClick={(e) => e.stopPropagation()}>
                {canMutate && (
                  <>
                    <button onClick={() => onEdit(c)} disabled={loading}>
                      Editar
                    </button>
                    <button
                      onClick={() => setShowConfirm(c)}
                      disabled={loading || !c.activo}
                    >
                      Desactivar
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {clientes.length === 0 && !loading && (
            <tr>
              <td colSpan={7} className="empty">
                No hay clientes
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {showConfirm && (
        <div className="confirm-modal">
          <div className="confirm-content">
            <p>
              ¿Desactivar cliente <strong>{showConfirm.nombre}</strong>?
            </p>
            <div className="confirm-actions">
              <button onClick={() => setShowConfirm(null)}>Cancelar</button>
              <button onClick={handleConfirmDelete} className="danger">
                Desactivar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
