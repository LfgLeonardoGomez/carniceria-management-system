import { useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useCompraStore } from '@/stores/compraStore'

export function CompraDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { selectedCompra, fetchCompra, deleteCompra, loading, clearSelected } = useCompraStore()

  useEffect(() => {
    if (id) {
      fetchCompra(id)
    }
    return () => clearSelected()
  }, [id])

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

  const handleAnular = async () => {
    if (!id) return
    if (!window.confirm('¿Está seguro de anular esta compra?')) return
    await deleteCompra(id)
  }

  if (loading) return <p className="text-gray-500">Cargando...</p>
  if (!selectedCompra) return <p className="text-gray-500">Compra no encontrada</p>

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Detalle de Compra</h2>
        <div className="flex gap-2">
          <button
            onClick={() => navigate(`/compras/${id}/editar`)}
            disabled={selectedCompra.estado === 'anulada'}
            className="rounded border px-4 py-2 hover:bg-gray-50 disabled:opacity-50"
          >
            Editar
          </button>
          <button
            onClick={handleAnular}
            disabled={selectedCompra.estado === 'anulada'}
            className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700 disabled:opacity-50"
          >
            Anular
          </button>
        </div>
      </div>

      <div className="rounded border p-4">
        <div className="mb-4 flex items-center gap-2">
          <span
            className={`rounded px-2 py-1 text-xs font-medium ${
              selectedCompra.estado === 'activa'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {selectedCompra.estado.toUpperCase()}
          </span>
        </div>

        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-gray-500">Fecha</dt>
            <dd className="font-medium">{selectedCompra.fecha}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Proveedor</dt>
            <dd className="font-medium">{selectedCompra.proveedor?.nombre || '-'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Cantidad</dt>
            <dd className="font-medium">{selectedCompra.cantidad_medias_reses} medias reses</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Peso Total</dt>
            <dd className="font-medium">{formatNumber(selectedCompra.peso_total)} kg</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Costo Total</dt>
            <dd className="font-medium">{formatCurrency(selectedCompra.costo_total)}</dd>
          </div>
          <div className="rounded bg-blue-50 p-2">
            <dt className="text-sm text-blue-700">Costo por Kilo</dt>
            <dd className="text-lg font-bold text-blue-800">
              {formatCurrency(selectedCompra.costo_por_kilo)}
            </dd>
          </div>
        </dl>

        {selectedCompra.observaciones && (
          <div className="mt-4">
            <dt className="text-sm text-gray-500">Observaciones</dt>
            <dd className="mt-1 whitespace-pre-wrap">{selectedCompra.observaciones}</dd>
          </div>
        )}
      </div>
    </div>
  )
}
