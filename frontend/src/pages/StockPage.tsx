import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useStockStore } from '@/stores/stockStore'
import type { StockItem, MovimientoStock } from '@/shared/types/stock'

export function StockPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthStore()
  const {
    stock,
    kardex,
    alertas,
    totalStock,
    totalKardex,
    loading,
    error,
    fetchStock,
    fetchKardex,
    fetchAlertas,
    ajustarStock,
    clearError,
  } = useStockStore()

  const [selectedProducto, setSelectedProducto] = useState<StockItem | null>(null)
  const [showKardex, setShowKardex] = useState(false)
  const [showAjuste, setShowAjuste] = useState(false)
  const [showAlertas, setShowAlertas] = useState(false)
  const [kardexSkip, setKardexSkip] = useState(0)
  const [stockSkip, setStockSkip] = useState(0)
  const [cantidad, setCantidad] = useState('')
  const [motivo, setMotivo] = useState('')

  const canAjustar = user?.rol === 'Administrador' || user?.rol === 'Encargado'
  const limit = 20

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    fetchStock({ skip: stockSkip, limit })
  }, [isAuthenticated, navigate, stockSkip, fetchStock])

  const handleSelectProducto = (item: StockItem) => {
    setSelectedProducto(item)
    setKardexSkip(0)
    setShowKardex(true)
    fetchKardex(item.producto_id, { skip: 0, limit })
  }

  const handleAjustar = (item: StockItem) => {
    setSelectedProducto(item)
    setCantidad('')
    setMotivo('')
    setShowAjuste(true)
  }

  const handleSubmitAjuste = async () => {
    if (!selectedProducto) return
    try {
      await ajustarStock({
        producto_id: selectedProducto.producto_id,
        cantidad_kilos: cantidad,
        motivo,
      })
      setShowAjuste(false)
      fetchStock({ skip: stockSkip, limit })
      if (showKardex) {
        fetchKardex(selectedProducto.producto_id, { skip: kardexSkip, limit })
      }
      fetchAlertas()
    } catch {
      // error handled in store
    }
  }

  const estadoBadge = (estado: string) => {
    if (estado === 'critico') return <span className="badge critico">Critico</span>
    if (estado === 'alerta') return <span className="badge alerta">Alerta</span>
    return <span className="badge ok">OK</span>
  }

  return (
    <div className="stock-page">
      <h1>Stock y Movimientos</h1>

      {error && (
        <div className="error-banner">
          {error}
          <button onClick={clearError}>×</button>
        </div>
      )}

      <div className="actions-bar">
        <button onClick={() => { setShowAlertas(true); fetchAlertas() }}>
          Alertas ({alertas.length})
        </button>
      </div>

      {loading && <div className="loading">Cargando...</div>}

      <table className="data-grid">
        <thead>
          <tr>
            <th>PLU</th>
            <th>Producto</th>
            <th>Stock Actual (kg)</th>
            <th>Stock Minimo</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {stock.map((item) => (
            <tr key={item.producto_id}>
              <td>{item.plu}</td>
              <td>{item.nombre}</td>
              <td>{item.stock_actual}</td>
              <td>{item.stock_minimo ?? '-'}</td>
              <td>{estadoBadge(item.estado)}</td>
              <td>
                <button onClick={() => handleSelectProducto(item)}>Kardex</button>
                {canAjustar && (
                  <button onClick={() => handleAjustar(item)}>Ajustar</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button disabled={stockSkip === 0} onClick={() => setStockSkip(Math.max(0, stockSkip - limit))}>
          Anterior
        </button>
        <span>
          {stockSkip + 1} - {Math.min(stockSkip + limit, totalStock)} de {totalStock}
        </span>
        <button disabled={stockSkip + limit >= totalStock} onClick={() => setStockSkip(stockSkip + limit)}>
          Siguiente
        </button>
      </div>

      {showKardex && selectedProducto && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Kardex: {selectedProducto.nombre}</h2>
            <table className="data-grid">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Cantidad (kg)</th>
                  <th>Stock Resultante</th>
                  <th>Referencia</th>
                  <th>Motivo</th>
                </tr>
              </thead>
              <tbody>
                {kardex.map((mov: MovimientoStock) => (
                  <tr key={mov.id}>
                    <td>{new Date(mov.fecha).toLocaleString()}</td>
                    <td>{mov.tipo}</td>
                    <td>{mov.cantidad_kilos}</td>
                    <td>{mov.stock_resultante}</td>
                    <td>{mov.referencia_tipo ?? '-'}</td>
                    <td>{mov.motivo ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pagination">
              <button disabled={kardexSkip === 0} onClick={() => {
                const newSkip = Math.max(0, kardexSkip - limit)
                setKardexSkip(newSkip)
                fetchKardex(selectedProducto.producto_id, { skip: newSkip, limit })
              }}>Anterior</button>
              <span>{kardexSkip + 1} - {Math.min(kardexSkip + limit, totalKardex)} de {totalKardex}</span>
              <button disabled={kardexSkip + limit >= totalKardex} onClick={() => {
                const newSkip = kardexSkip + limit
                setKardexSkip(newSkip)
                fetchKardex(selectedProducto.producto_id, { skip: newSkip, limit })
              }}>Siguiente</button>
            </div>
            <button onClick={() => setShowKardex(false)}>Cerrar</button>
          </div>
        </div>
      )}

      {showAjuste && selectedProducto && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Ajuste de Stock: {selectedProducto.nombre}</h2>
            <p>Stock actual: {selectedProducto.stock_actual} kg</p>
            <label>
              Cantidad (kg):
              <input
                type="number"
                step="0.001"
                value={cantidad}
                onChange={(e) => setCantidad(e.target.value)}
                placeholder="Positivo para entrada, negativo para salida"
              />
            </label>
            <label>
              Motivo:
              <input
                type="text"
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Motivo del ajuste"
              />
            </label>
            <div className="modal-actions">
              <button onClick={handleSubmitAjuste} disabled={loading || !cantidad || !motivo}>
                Guardar
              </button>
              <button onClick={() => setShowAjuste(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}

      {showAlertas && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Alertas de Stock</h2>
            {alertas.length === 0 ? (
              <p>No hay alertas de stock.</p>
            ) : (
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>PLU</th>
                    <th>Producto</th>
                    <th>Stock Actual</th>
                    <th>Stock Minimo</th>
                    <th>Estado</th>
                    <th>Accion</th>
                  </tr>
                </thead>
                <tbody>
                  {alertas.map((alerta) => (
                    <tr key={alerta.producto_id}>
                      <td>{alerta.plu}</td>
                      <td>{alerta.nombre}</td>
                      <td>{alerta.stock_actual}</td>
                      <td>{alerta.stock_minimo}</td>
                      <td>{estadoBadge(alerta.estado)}</td>
                      <td>
                        <button onClick={() => {
                          const item = stock.find(s => s.producto_id === alerta.producto_id)
                          if (item) handleSelectProducto(item)
                          setShowAlertas(false)
                        }}>Ver Kardex</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <button onClick={() => setShowAlertas(false)}>Cerrar</button>
          </div>
        </div>
      )}
    </div>
  )
}
