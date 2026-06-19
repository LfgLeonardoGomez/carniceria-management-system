import type { Cliente } from '@/shared/types/cliente'

interface ClienteDetailProps {
  cliente: Cliente
  historial: { items: unknown[]; total: number }
  loading: boolean
  onBack: () => void
}

export function ClienteDetail({ cliente, historial, loading, onBack }: ClienteDetailProps) {
  return (
    <div className="cliente-detail">
      <button onClick={onBack} className="back-btn">
        ← Volver
      </button>

      <div className="profile-card">
        <h2>{cliente.nombre} {cliente.apellido || ''}</h2>
        <div className="profile-fields">
          <div className="field">
            <span className="label">Razón Social:</span>
            <span className="value">{cliente.razon_social || '-'}</span>
          </div>
          <div className="field">
            <span className="label">CUIT:</span>
            <span className="value">{cliente.cuit || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Teléfono:</span>
            <span className="value">{cliente.telefono || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Email:</span>
            <span className="value">{cliente.email || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Dirección:</span>
            <span className="value">{cliente.direccion || '-'}</span>
          </div>
          <div className="field">
            <span className="label">Tipo:</span>
            <span className="value">{cliente.tipo_cliente}</span>
          </div>
          <div className="field">
            <span className="label">Estado:</span>
            <span className="value">{cliente.activo ? 'Activo' : 'Inactivo'}</span>
          </div>
        </div>
      </div>

      <div className="saldo-card">
        <h3>Saldo Actual</h3>
        <div className="saldo-value">{cliente.saldo_actual}</div>
        <div className="limite-value">
          Límite: {cliente.limite_cuenta_corriente}
        </div>
      </div>

      <div className="historial-section">
        <h3>Historial de Compras</h3>
        <div className="historial-total">Total: {historial.total} ventas</div>
        {loading && <div className="loading">Cargando historial...</div>}
        {historial.items.length === 0 && !loading && (
          <div className="empty">No hay compras registradas</div>
        )}
        {historial.items.length > 0 && (
          <table className="historial-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {historial.items.map((v: unknown) => {
                const venta = v as { id: string; fecha: string; total: string; estado: string }
                return (
                  <tr key={venta.id}>
                    <td>{venta.fecha}</td>
                    <td>{venta.total}</td>
                    <td>{venta.estado}</td>
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
