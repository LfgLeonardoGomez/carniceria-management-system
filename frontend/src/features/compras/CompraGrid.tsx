import { useNavigate } from 'react-router-dom'
import { useCompraStore } from '@/stores/compraStore'
import type { Compra } from '@/shared/types/compra'

export function CompraGrid() {
  const navigate = useNavigate()
  const { compras, totalCompras, loading, filters, setFilters } = useCompraStore()

  const handleRowClick = (compra: Compra) => {
    navigate(`/compras/${compra.id}`)
  }

  const formatCurrency = (value: string) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
    }).format(Number(value))
  }

  const formatNumber = (value: string) => {
    return new Intl.NumberFormat('es-AR', {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    }).format(Number(value))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Compras de Media Res</h2>
        <button
          onClick={() => navigate('/compras/nueva')}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          Nueva Compra
        </button>
      </div>

      <div className="flex gap-4">
        <input
          type="date"
          placeholder="Fecha desde"
          value={filters.fecha_desde || ''}
          onChange={(e) => setFilters({ fecha_desde: e.target.value || undefined })}
          className="rounded border p-2"
        />
        <input
          type="date"
          placeholder="Fecha hasta"
          value={filters.fecha_hasta || ''}
          onChange={(e) => setFilters({ fecha_hasta: e.target.value || undefined })}
          className="rounded border p-2"
        />
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={filters.incluir_anuladas || false}
            onChange={(e) => setFilters({ incluir_anuladas: e.target.checked })}
          />
          Incluir anuladas
        </label>
      </div>

      {loading && <p className="text-gray-500">Cargando...</p>}

      <div className="overflow-x-auto rounded border">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-2">Fecha</th>
              <th className="px-4 py-2">Proveedor</th>
              <th className="px-4 py-2">Cantidad</th>
              <th className="px-4 py-2">Peso Total (kg)</th>
              <th className="px-4 py-2">Costo Total</th>
              <th className="px-4 py-2">Costo/kg</th>
              <th className="px-4 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {compras.map((compra) => (
              <tr
                key={compra.id}
                onClick={() => handleRowClick(compra)}
                className="cursor-pointer border-t hover:bg-gray-50"
              >
                <td className="px-4 py-2">{compra.fecha}</td>
                <td className="px-4 py-2">{compra.proveedor?.nombre || '-'}</td>
                <td className="px-4 py-2">{compra.cantidad_medias_reses}</td>
                <td className="px-4 py-2">{formatNumber(compra.peso_total)}</td>
                <td className="px-4 py-2">{formatCurrency(compra.costo_total)}</td>
                <td className="px-4 py-2 font-semibold text-blue-700">
                  {formatCurrency(compra.costo_por_kilo)}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded px-2 py-1 text-xs font-medium ${
                      compra.estado === 'activa'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {compra.estado}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          Total: {totalCompras} compras
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setFilters({ skip: Math.max(0, (filters.skip || 0) - (filters.limit || 20)) })}
            disabled={(filters.skip || 0) === 0}
            className="rounded border px-3 py-1 disabled:opacity-50"
          >
            Anterior
          </button>
          <button
            onClick={() => setFilters({ skip: (filters.skip || 0) + (filters.limit || 20) })}
            disabled={(filters.skip || 0) + (filters.limit || 20) >= totalCompras}
            className="rounded border px-3 py-1 disabled:opacity-50"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  )
}
