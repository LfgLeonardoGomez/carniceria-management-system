import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCompraStore } from '@/stores/compraStore'

interface CompraFormProps {
  compraId?: string
}

export function CompraForm({ compraId }: CompraFormProps) {
  const navigate = useNavigate()
  const { selectedCompra, fetchCompra, createCompra, updateCompra, loading, error, clearError } = useCompraStore()

  const [fecha, setFecha] = useState('')
  const [proveedorId, setProveedorId] = useState('')
  const [cantidad, setCantidad] = useState('1')
  const [peso, setPeso] = useState('')
  const [costo, setCosto] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [costoPreview, setCostoPreview] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (compraId) {
      fetchCompra(compraId)
    }
  }, [compraId])

  useEffect(() => {
    if (selectedCompra && compraId) {
      setFecha(selectedCompra.fecha)
      setProveedorId(selectedCompra.proveedor_id)
      setCantidad(String(selectedCompra.cantidad_medias_reses))
      setPeso(String(selectedCompra.peso_total))
      setCosto(String(selectedCompra.costo_total))
      setObservaciones(selectedCompra.observaciones || '')
    }
  }, [selectedCompra, compraId])

  useEffect(() => {
    const pesoNum = parseFloat(peso)
    const costoNum = parseFloat(costo)
    if (pesoNum > 0 && costoNum > 0) {
      setCostoPreview((costoNum / pesoNum).toFixed(3))
    } else {
      setCostoPreview(null)
    }
  }, [peso, costo])

  const validate = () => {
    if (!fecha) return 'La fecha es obligatoria'
    if (!proveedorId) return 'El proveedor es obligatorio'
    if (parseInt(cantidad) < 1) return 'La cantidad debe ser al menos 1'
    if (parseFloat(peso) <= 0) return 'El peso debe ser mayor a 0'
    if (parseFloat(costo) <= 0) return 'El costo debe ser mayor a 0'
    const fechaValue = new Date(fecha)
    if (fechaValue > new Date()) return 'La fecha no puede ser futura'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setFormError(null)

    const validationError = validate()
    if (validationError) {
      setFormError(validationError)
      return
    }

    const dto = {
      fecha,
      proveedor_id: proveedorId,
      cantidad_medias_reses: parseInt(cantidad),
      peso_total: peso,
      costo_total: costo,
      observaciones: observaciones || null,
    }

    try {
      if (compraId) {
        await updateCompra(compraId, dto)
      } else {
        await createCompra(dto)
      }
      navigate('/compras')
    } catch {
      // Error ya está en el store
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h2 className="text-2xl font-bold">
        {compraId ? 'Editar Compra' : 'Nueva Compra'}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Fecha</label>
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            className="w-full rounded border p-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Proveedor ID</label>
          <input
            type="text"
            value={proveedorId}
            onChange={(e) => setProveedorId(e.target.value)}
            className="w-full rounded border p-2"
            placeholder="UUID del proveedor"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Cantidad de Medias Reses</label>
          <input
            type="number"
            min="1"
            value={cantidad}
            onChange={(e) => setCantidad(e.target.value)}
            className="w-full rounded border p-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Peso Total (kg)</label>
          <input
            type="number"
            step="0.001"
            min="0.001"
            value={peso}
            onChange={(e) => setPeso(e.target.value)}
            className="w-full rounded border p-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium">Costo Total ($)</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={costo}
            onChange={(e) => setCosto(e.target.value)}
            className="w-full rounded border p-2"
            required
          />
        </div>

        {costoPreview && (
          <div className="rounded bg-blue-50 p-3 text-blue-800">
            <span className="font-semibold">Costo por kilo calculado: </span>
            ${costoPreview}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium">Observaciones</label>
          <textarea
            value={observaciones}
            onChange={(e) => setObservaciones(e.target.value)}
            className="w-full rounded border p-2"
            rows={3}
          />
        </div>

        {(formError || error) && (
          <div className="rounded bg-red-50 p-3 text-red-700">
            {formError || error}
          </div>
        )}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Guardando...' : compraId ? 'Actualizar' : 'Crear'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/compras')}
            className="rounded border px-4 py-2 hover:bg-gray-50"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}
