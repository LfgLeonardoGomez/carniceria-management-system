import { useState, useEffect } from 'react'
import type { Cliente, ClienteCreate, ClienteUpdate } from '@/shared/types/cliente'

interface ClienteFormProps {
  cliente: Cliente | null
  onSubmit: (data: ClienteCreate | ClienteUpdate) => void
  onCancel: () => void
  loading: boolean
}

const TIPOS_CLIENTE = [
  { value: 'publico_general', label: 'Público General' },
  { value: 'mayorista', label: 'Mayorista' },
  { value: 'especial', label: 'Especial' },
]

export function ClienteForm({ cliente, onSubmit, onCancel, loading }: ClienteFormProps) {
  const [nombre, setNombre] = useState('')
  const [apellido, setApellido] = useState('')
  const [razonSocial, setRazonSocial] = useState('')
  const [cuit, setCuit] = useState('')
  const [telefono, setTelefono] = useState('')
  const [email, setEmail] = useState('')
  const [direccion, setDireccion] = useState('')
  const [tipoCliente, setTipoCliente] = useState('publico_general')
  const [limite, setLimite] = useState('0.0000')
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (cliente) {
      setNombre(cliente.nombre)
      setApellido(cliente.apellido || '')
      setRazonSocial(cliente.razon_social || '')
      setCuit(cliente.cuit || '')
      setTelefono(cliente.telefono || '')
      setEmail(cliente.email || '')
      setDireccion(cliente.direccion || '')
      setTipoCliente(cliente.tipo_cliente)
      setLimite(cliente.limite_cuenta_corriente)
    } else {
      setNombre('')
      setApellido('')
      setRazonSocial('')
      setCuit('')
      setTelefono('')
      setEmail('')
      setDireccion('')
      setTipoCliente('publico_general')
      setLimite('0.0000')
    }
    setErrors({})
  }, [cliente])

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
      apellido: apellido.trim() || null,
      razon_social: razonSocial.trim() || null,
      cuit: cuit.trim() || null,
      telefono: telefono.trim() || null,
      email: email.trim() || null,
      direccion: direccion.trim() || null,
      tipo_cliente: tipoCliente,
      limite_cuenta_corriente: limite.trim() || undefined,
    }

    onSubmit(payload)
  }

  return (
    <div className="cliente-form-modal">
      <h2>{cliente ? 'Editar Cliente' : 'Nuevo Cliente'}</h2>
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
            Apellido
            <input
              type="text"
              value={apellido}
              onChange={(e) => setApellido(e.target.value)}
              disabled={loading}
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Razón Social
            <input
              type="text"
              value={razonSocial}
              onChange={(e) => setRazonSocial(e.target.value)}
              disabled={loading}
            />
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

        <div className="form-row">
          <label>
            Tipo de Cliente
            <select
              value={tipoCliente}
              onChange={(e) => setTipoCliente(e.target.value)}
              disabled={loading}
            >
              {TIPOS_CLIENTE.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="form-row">
          <label>
            Límite Cuenta Corriente
            <input
              type="text"
              value={limite}
              onChange={(e) => setLimite(e.target.value)}
              disabled={loading}
            />
          </label>
        </div>

        <div className="form-actions">
          <button type="button" onClick={onCancel} disabled={loading}>
            Cancelar
          </button>
          <button type="submit" disabled={loading}>
            {loading ? 'Guardando...' : cliente ? 'Actualizar' : 'Crear'}
          </button>
        </div>
      </form>
    </div>
  )
}
