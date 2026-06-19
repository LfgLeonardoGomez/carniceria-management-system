import { useState } from 'react'
import type { Proveedor } from '@/shared/types/proveedor'

interface ProveedoresGridProps {
  proveedores: Proveedor[]
  total: number
  loading: boolean
  onEdit: (proveedor: Proveedor) => void
  onDelete: (proveedor: Proveedor) => void
  onSearch: (q: string) => void
  onNavigate: (proveedor: Proveedor) => void
  search: string
  canMutate: boolean
}

export function ProveedoresGrid({
  proveedores,
  total,
  loading,
  onEdit,
  onDelete,
  onSearch,
  onNavigate,
  search,
  canMutate,
}: ProveedoresGridProps) {
  const [showConfirm, setShowConfirm] = useState<Proveedor | null>(null)

  const handleConfirmDelete = () => {
    if (showConfirm) {
      onDelete(showConfirm)
      setShowConfirm(null)
    }
  }

  return (
    <div className="proveedores-grid">
      <div className="filters-bar">
        <input
          type="text"
          placeholder="Buscar por nombre..."
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="total-info">Total: {total} proveedores</div>

      {loading && <div className="loading">Cargando...</div>}

      <table className="proveedores-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>CUIT</th>
            <th>Teléfono</th>
            <th>Email</th>
            <th>Dirección</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {proveedores.map((p) => (
            <tr
              key={p.id}
              className={p.activo ? '' : 'inactive'}
              onClick={() => onNavigate(p)}
              style={{ cursor: 'pointer' }}
            >
              <td>{p.nombre}</td>
              <td>{p.cuit || '-'}</td>
              <td>{p.telefono || '-'}</td>
              <td>{p.email || '-'}</td>
              <td>{p.direccion || '-'}</td>
              <td>{p.activo ? 'Activo' : 'Inactivo'}</td>
              <td onClick={(e) => e.stopPropagation()}>
                {canMutate && (
                  <>
                    <button onClick={() => onEdit(p)} disabled={loading}>
                      Editar
                    </button>
                    <button
                      onClick={() => setShowConfirm(p)}
                      disabled={loading || !p.activo}
                    >
                      Desactivar
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {proveedores.length === 0 && !loading && (
            <tr>
              <td colSpan={7} className="empty">
                No hay proveedores
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {showConfirm && (
        <div className="confirm-modal">
          <div className="confirm-content">
            <p>
              ¿Desactivar proveedor <strong>{showConfirm.nombre}</strong>?
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
