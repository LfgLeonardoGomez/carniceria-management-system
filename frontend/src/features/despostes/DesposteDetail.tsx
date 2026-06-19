import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDesposteStore } from '@/stores/desposteStore'

export function DesposteDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedDesposte, loading, error, fetchDesposte, clearSelected } = useDesposteStore()

  useEffect(() => {
    if (id) {
      fetchDesposte(id)
    }
    return () => {
      clearSelected()
    }
  }, [id])

  if (loading) {
    return <div className="p-4">Cargando desposte...</div>
  }

  if (!selectedDesposte) {
    return (
      <div className="p-4">
        {error && <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">{error}</div>}
        <p>Desposte no encontrado</p>
        <button className="mt-2 text-blue-600 underline" onClick={() => navigate('/despostes')}>
          Volver a despostes
        </button>
      </div>
    )
  }

  const d = selectedDesposte

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Desposte #{d.id.slice(0, 8)}</h2>
        <button className="text-blue-600 underline" onClick={() => navigate('/despostes')}>
          Volver
        </button>
      </div>

      {error && <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">{error}</div>}

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-500">Fecha</p>
          <p className="font-medium">{d.fecha}</p>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-500">Estado</p>
          <p className="font-medium">
            <span
              className={`px-2 py-1 rounded text-sm ${
                d.estado === 'finalizado'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {d.estado === 'en_proceso' ? 'En proceso' : 'Finalizado'}
            </span>
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-500">Compra origen</p>
          <p className="font-medium">
            {d.compra?.proveedor?.nombre ?? '—'} — {d.compra?.peso_total} kg — ${d.compra?.costo_total}
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-500">Operador</p>
          <p className="font-medium">
            {d.operador?.nombre ?? '—'} {d.operador?.apellido ?? ''}
          </p>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-500">Rendimiento total</p>
          <p className="font-medium">{d.rendimiento_total} kg</p>
        </div>
        <div className="p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-500">Merma</p>
          <p className="font-medium">{d.merma} kg</p>
        </div>
      </div>

      <h3 className="text-lg font-bold mb-2">Cortes</h3>
      <table className="w-full border mb-4">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2 border text-left">Corte</th>
            <th className="p-2 border text-right">Kilos</th>
            <th className="p-2 border text-right">% Rend.</th>
            <th className="p-2 border text-right">Costo Asignado</th>
            <th className="p-2 border text-right">Costo/kg</th>
            <th className="p-2 border text-left">Producto</th>
          </tr>
        </thead>
        <tbody>
          {d.cortes.map((c) => (
            <tr key={c.id}>
              <td className="p-2 border capitalize">{c.tipo_corte.replace('_', ' ')}</td>
              <td className="p-2 border text-right">{c.kilos_obtenidos}</td>
              <td className="p-2 border text-right">{c.porcentaje_rendimiento}%</td>
              <td className="p-2 border text-right">${c.costo_asignado}</td>
              <td className="p-2 border text-right">${c.costo_final_por_kilo}</td>
              <td className="p-2 border">{c.producto?.nombre ?? '—'}</td>
            </tr>
          ))}
          {d.cortes.length === 0 && (
            <tr>
              <td colSpan={6} className="p-4 text-center text-gray-500">
                No hay cortes registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {d.estado === 'finalizado' && d.movimientos_stock.length > 0 && (
        <>
          <h3 className="text-lg font-bold mb-2">Movimientos de Stock Generados</h3>
          <table className="w-full border">
            <thead>
              <tr className="bg-gray-100">
                <th className="p-2 border text-left">Tipo</th>
                <th className="p-2 border text-right">Cantidad (kg)</th>
                <th className="p-2 border text-right">Stock Resultante</th>
                <th className="p-2 border text-left">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {d.movimientos_stock.map((m) => (
                <tr key={m.id}>
                  <td className="p-2 border">{m.tipo}</td>
                  <td className="p-2 border text-right">{m.cantidad_kilos}</td>
                  <td className="p-2 border text-right">{m.stock_resultante}</td>
                  <td className="p-2 border">{m.fecha}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
