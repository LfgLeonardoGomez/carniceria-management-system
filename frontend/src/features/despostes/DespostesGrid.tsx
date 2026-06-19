import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDesposteStore } from '@/stores/desposteStore'

export function DespostesGrid() {
  const navigate = useNavigate()
  const { despostes, totalDespostes, loading, error, filters, fetchDespostes, setFilters } =
    useDesposteStore()

  useEffect(() => {
    fetchDespostes()
  }, [filters.skip, filters.limit])

  if (loading && despostes.length === 0) {
    return <div className="p-4">Cargando despostes...</div>
  }

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Despostes</h2>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded"
          onClick={() => navigate('/despostes/nuevo')}
        >
          Nuevo Desposte
        </button>
      </div>

      {error && (
        <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">{error}</div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full border">
          <thead>
            <tr className="bg-gray-100">
              <th className="p-2 border text-left">Fecha</th>
              <th className="p-2 border text-left">Compra</th>
              <th className="p-2 border text-left">Operador</th>
              <th className="p-2 border text-left">Estado</th>
              <th className="p-2 border text-right">Rendimiento (kg)</th>
              <th className="p-2 border text-right">Merma (kg)</th>
              <th className="p-2 border text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {despostes.map((d) => (
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="p-2 border">{d.fecha}</td>
                <td className="p-2 border">
                  {d.compra?.proveedor?.nombre ?? '—'}
                </td>
                <td className="p-2 border">
                  {d.operador?.nombre ?? '—'} {d.operador?.apellido ?? ''}
                </td>
                <td className="p-2 border">
                  <span
                    className={`px-2 py-1 rounded text-sm ${
                      d.estado === 'finalizado'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {d.estado === 'en_proceso' ? 'En proceso' : 'Finalizado'}
                  </span>
                </td>
                <td className="p-2 border text-right">{d.rendimiento_total}</td>
                <td className="p-2 border text-right">{d.merma}</td>
                <td className="p-2 border text-center">
                  <button
                    className="text-blue-600 hover:underline"
                    onClick={() => navigate(`/despostes/${d.id}`)}
                  >
                    Ver
                  </button>
                </td>
              </tr>
            ))}
            {despostes.length === 0 && (
              <tr>
                <td colSpan={7} className="p-4 text-center text-gray-500">
                  No hay despostes registrados
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center mt-4">
        <span className="text-sm text-gray-600">
          Total: {totalDespostes}
        </span>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 border rounded disabled:opacity-50"
            disabled={filters.skip === 0}
            onClick={() => setFilters({ skip: Math.max(0, (filters.skip ?? 0) - (filters.limit ?? 20)) })}
          >
            Anterior
          </button>
          <button
            className="px-3 py-1 border rounded disabled:opacity-50"
            disabled={(filters.skip ?? 0) + (filters.limit ?? 20) >= totalDespostes}
            onClick={() => setFilters({ skip: (filters.skip ?? 0) + (filters.limit ?? 20) })}
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  )
}
