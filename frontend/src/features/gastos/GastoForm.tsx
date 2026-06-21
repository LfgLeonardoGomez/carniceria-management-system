import { useState, useEffect } from 'react'
import type { Gasto, GastoCreate, GastoUpdate, CategoriaGasto, MedioPagoGasto } from '@/shared/types/gasto'
import { CATEGORIAS_GASTO, CATEGORIAS_GASTO_LABELS, MEDIOS_PAGO_GASTO, MEDIOS_PAGO_GASTO_LABELS } from '@/shared/types/gasto'

interface GastoFormProps {
  gasto: Gasto | null
  onSubmit: (data: GastoCreate | GastoUpdate) => void
  onCancel: () => void
  loading: boolean
  error: string | null
}

export function GastoForm({ gasto, onSubmit, onCancel, loading, error }: GastoFormProps) {
  const today = new Date().toISOString().split('T')[0]

  const [fecha, setFecha] = useState(today)
  const [categoria, setCategoria] = useState<CategoriaGasto>('alquiler')
  const [descripcion, setDescripcion] = useState('')
  const [importe, setImporte] = useState('')
  const [medioPago, setMedioPago] = useState<MedioPagoGasto>('transferencia')
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (gasto) {
      setFecha(gasto.fecha)
      setCategoria(gasto.categoria)
      setDescripcion(gasto.descripcion ?? '')
      setImporte(gasto.importe)
      setMedioPago(gasto.medio_pago)
    } else {
      setFecha(today)
      setCategoria('alquiler')
      setDescripcion('')
      setImporte('')
      setMedioPago('transferencia')
    }
    setErrors({})
  }, [gasto])

  const validate = () => {
    const newErrors: Record<string, string> = {}

    if (!fecha) newErrors.fecha = 'La fecha es obligatoria'

    if (!importe || importe.trim() === '') {
      newErrors.importe = 'El importe es obligatorio'
    } else {
      const val = parseFloat(importe)
      if (isNaN(val) || val <= 0) {
        newErrors.importe = 'El importe debe ser un número mayor a 0'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    // Format importe as string with 2 decimal places for the backend
    const importeFormatted = parseFloat(importe).toFixed(2)

    const payload: GastoCreate = {
      fecha,
      categoria,
      descripcion: descripcion.trim() || null,
      importe: importeFormatted,
      medio_pago: medioPago,
    }

    onSubmit(payload)
  }

  return (
    <div className="gasto-form-modal">
      <h2>{gasto ? 'Editar Gasto' : 'Nuevo Gasto'}</h2>
      {error && <div className="error-banner">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Fecha *
            <input
              type="date"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              disabled={loading}
            />
            {errors.fecha && <span className="error">{errors.fecha}</span>}
          </label>
        </div>

        <div className="form-row">
          <label>
            Categoría *
            <select
              value={categoria}
              onChange={(e) => setCategoria(e.target.value as CategoriaGasto)}
              disabled={loading}
            >
              {CATEGORIAS_GASTO.map((cat) => (
                <option key={cat} value={cat}>
                  {CATEGORIAS_GASTO_LABELS[cat]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-row">
          <label>
            Descripción
            <input
              type="text"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              disabled={loading}
              placeholder="Descripción opcional"
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Importe *
            <input
              type="number"
              value={importe}
              onChange={(e) => setImporte(e.target.value)}
              disabled={loading}
              min="0.01"
              step="0.01"
              placeholder="0.00"
            />
            {errors.importe && <span className="error">{errors.importe}</span>}
          </label>
        </div>

        <div className="form-row">
          <label>
            Medio de pago *
            <select
              value={medioPago}
              onChange={(e) => setMedioPago(e.target.value as MedioPagoGasto)}
              disabled={loading}
            >
              {MEDIOS_PAGO_GASTO.map((m) => (
                <option key={m} value={m}>
                  {MEDIOS_PAGO_GASTO_LABELS[m]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-actions">
          <button type="button" onClick={onCancel} disabled={loading}>
            Cancelar
          </button>
          <button type="submit" disabled={loading}>
            {loading ? 'Guardando...' : gasto ? 'Actualizar' : 'Registrar gasto'}
          </button>
        </div>
      </form>
    </div>
  )
}
