import { useState } from 'react'
import { ROLES } from '@/shared/types/usuario'
import type { UsuarioCreate } from '@/shared/types/usuario'

interface UsuarioCreateModalProps {
  onSubmit: (dto: UsuarioCreate) => Promise<void>
  onCancel: () => void
  loading: boolean
  error: string | null
}

export function UsuarioCreateModal({ onSubmit, onCancel, loading, error }: UsuarioCreateModalProps) {
  const [form, setForm] = useState<UsuarioCreate>({
    nombre: '',
    apellido: '',
    email: '',
    rol_id: '',
  })
  const [emailError, setEmailError] = useState<string | null>(null)

  const handleChange = (field: keyof UsuarioCreate, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (field === 'email') {
      setEmailError(null)
    }
  }

  const isEmailValid = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailError(null)
    if (!isEmailValid(form.email)) {
      setEmailError('Email inválido')
      return
    }
    if (!form.rol_id) {
      return
    }
    await onSubmit(form)
  }

  return (
    <div className="modal-overlay" onClick={onCancel} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Nuevo usuario</h2>
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="create-nombre">Nombre</label>
            <input
              id="create-nombre"
              value={form.nombre}
              onChange={(e) => handleChange('nombre', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="create-apellido">Apellido</label>
            <input
              id="create-apellido"
              value={form.apellido}
              onChange={(e) => handleChange('apellido', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="create-email">Email</label>
            <input
              id="create-email"
              type="email"
              value={form.email}
              onChange={(e) => handleChange('email', e.target.value)}
            />
            {emailError && <span className="error">{emailError}</span>}
          </div>
          <div className="form-group">
            <label htmlFor="create-rol">Rol</label>
            <select
              id="create-rol"
              value={form.rol_id}
              onChange={(e) => handleChange('rol_id', e.target.value)}
            >
              <option value="">Seleccionar rol</option>
              {ROLES.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.nombre}
                </option>
              ))}
            </select>
          </div>
          {error && <div className="error-banner">{error}</div>}
          <div className="modal-actions">
            <button type="submit" disabled={loading || !form.rol_id}>
              {loading ? 'Creando...' : 'Crear'}
            </button>
            <button type="button" onClick={onCancel}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
