import type { Proveedor } from '@/shared/types/proveedor'

interface ProveedorDetailProps {
  proveedor: Proveedor
  historial: { items: unknown[]; total: number }
  loading: boolean
  onBack: () => void
  onEdit: () => void
  canMutate: boolean
}

export function ProveedorDetail({ proveedor, historial, loading, onBack, onEdit, canMutate }: ProveedorDetailProps) {
  return (
    <div className="proveedor-detail">
      <button onClick={onBack} className="back-btn">
        ← Volver
      </button>

      <div className="profile-card">
        <div className="profile-header">
          <h2>{proveedor.nombre}</h2>
          {canMutate && (
            <button onClick={onEdit} className="edit-btn">
              Editar
            </button>
          )}
        </div>
        <div className="profile-fields">
          <div className="field">
            <span className="label">CUIT:</span>
            <span className="value">{proveedor.cuit || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Teléfono:</span>
            <span className="value">{proveedor.telefono || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Email:</span>
            <span className="value">{proveedor.email || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Dirección:</span>
            <span className="value">{proveedor.direccion || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Estado:</span>
            <span className="value">{proveedor.activo ? 'Activo' : 'Inactivo'}</span>
          </div>
        </div>
      </div>

      <div className="historial-section">
        <h3>Historial de Compras</h3>
        <div className="historial-total">Total: {historial.total} compras</div>
        {loading && <div className="loading">Cargando historial...</div>}
        {historial.items.length === 0 && !loading && (
          <div className="empty">Sin compras registradas</div>
        )}
        {historial.items.length > 0 && (
          <table className="historial-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Cantidad Medias Reses</th>
                <th>Peso Total</th>
                <th>Costo Total</th>
                <th>Costo por Kilo</th>
                <th>Observaciones</th>
              </tr>
            </thead>
            <tbody>
              {historial.items.map((c: unknown) => {
                const compra = c as {
                  id: string
                  fecha: string
                  cantidad_medias_reses: number
                  peso_total: string
                  costo_total: string
                  costo_por_kilo: string
                  observaciones: string | null
                }
                return (
                  <tr key={compra.id}>
                    <td>{compra.fecha}</td>
                    <td>{compra.cantidad_medias_reses}</td>
                    <td>{compra.peso_total}</td>
                    <td>{compra.costo_total}</td>
                    <td>{compra.costo_por_kilo}</td>
                    <td>{compra.observaciones || '-'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
