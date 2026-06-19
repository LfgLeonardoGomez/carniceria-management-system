import { useState, useEffect } from 'react'
import type { Proveedor, ProveedorCreate, ProveedorUpdate } from '@/shared/types/proveedor'

interface ProveedorFormProps {
  proveedor: Proveedor | null
  onSubmit: (data: ProveedorCreate | ProveedorUpdate) => void
  onCancel: () => void
  loading: boolean
  error: string | null
}

export function ProveedorForm({ proveedor, onSubmit, onCancel, loading, error }: ProveedorFormProps) {
  const [nombre, setNombre] = useState('')
  const [cuit, setCuit] = useState('')
  const [telefono, setTelefono] = useState('')
  const [email, setEmail] = useState('')
  const [direccion, setDireccion] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (proveedor) {
      setNombre(proveedor.nombre)
      setCuit(proveedor.cuit || '')
      setTelefono(proveedor.telefono || '')
      setEmail(proveedor.email || '')
      setDireccion(proveedor.direccion || '')
    } else {
      setNombre('')
      setCuit('')
      setTelefono('')
      setEmail('')
      setDireccion('')
    }
    setErrors({})
  }, [proveedor])

  const validate = () => {
    const newErrors: Record<string, string> = {}
    if (!nombre.trim()) newErrors.nombre = 'El nombre es obligatorio'
    if (cuit && !/^\d{11}$/.test(cuit.replace(/[^\d]/g, ''))) {
      newErrors.cuit = 'CUIT inválido (debe tener 11 dígitos)'
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Email inválido'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    const payload = {
      nombre: nombre.trim(),
      cuit: cuit.trim() || null,
      telefono: telefono.trim() || null,
      email: email.trim() || null,
      direccion: direccion.trim() || null,
    }

    onSubmit(payload)
  }

  return (
    <div className="proveedor-form-modal">
      <h2>{proveedor ? 'Editar Proveedor' : 'Nuevo Proveedor'}</h2>
      {error && <div className="error-banner">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Nombre *
            <input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              disabled={loading}
            />
            {errors.nombre && <span className="error">{errors.nombre}</span>}
          </label>
        </div>

        <div className="form-row">
          <label>
            CUIT
            <input
              type="text"
              value={cuit}
              onChange={(e) => setCuit(e.target.value)}
              disabled={loading}
              placeholder="20-12345678-9"
            />
            {errors.cuit && <span className="error">{errors.cuit}</span>}
          </label>
        </div>

        <div className="form-row">
          <label>
            Teléfono
            <input
              type="text"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              disabled={loading}
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Email
            <input
              type="text"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            {errors.email && <span className="error">{errors.email}</span>}
          </label>
        </div>

        <div className="form-row">
          <label>
            Dirección
            <input
              type="text"
              value={direccion}
              onChange={(e) => setDireccion(e.target.value)}
              disabled={loading}
            />
          </label>
        </div>

        <div className="form-actions">
          <button type="button" onClick={onCancel} disabled={loading}>
            Cancelar
          </button>
          <button type="submit" disabled={loading}>
            {loading ? 'Guardando...' : proveedor ? 'Actualizar' : 'Crear'}
          </button>
        </div>
      </form>
    </div>
  )
}
