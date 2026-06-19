import { useState, useEffect } from 'react'
import { ROLES } from '@/shared/types/usuario'
import type { UsuarioPublic, UsuarioUpdate } from '@/shared/types/usuario'

interface UsuarioEditModalProps {
  usuario: UsuarioPublic
  onSubmit: (dto: UsuarioUpdate) => Promise<void>
  onCancel: () => void
  loading: boolean
  error: string | null
}

export function UsuarioEditModal({ usuario, onSubmit, onCancel, loading, error }: UsuarioEditModalProps) {
  const [form, setForm] = useState<UsuarioUpdate>({})
  const [emailError, setEmailError] = useState<string | null>(null)

  useEffect(() => {
    setForm({
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      email: usuario.email,
      rol_id: ROLES.find((r) => r.nombre === usuario.rol)?.id,
    })
  }, [usuario])

  const handleChange = (field: keyof UsuarioUpdate, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value || undefined }))
    if (field === 'email') {
      setEmailError(null)
    }
  }

  const isEmailValid = (email: string | undefined) => {
    if (!email) return true
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailError(null)
    if (!isEmailValid(form.email)) {
      setEmailError('Email inválido')
      return
    }
    await onSubmit(form)
  }

  const selectedRolName = ROLES.find((r) => r.id === form.rol_id)?.nombre || usuario.rol || '-'

  return (
    <div className="modal-overlay" onClick={onCancel} role="dialog" aria-modal="true">
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Editar usuario</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="edit-nombre">Nombre</label>
            <input
              id="edit-nombre"
              value={form.nombre || ''}
              onChange={(e) => handleChange('nombre', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="edit-apellido">Apellido</label>
            <input
              id="edit-apellido"
              value={form.apellido || ''}
              onChange={(e) => handleChange('apellido', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="edit-email">Email</label>
            <input
              id="edit-email"
              type="email"
              value={form.email || ''}
              onChange={(e) => handleChange('email', e.target.value)}
            />
            {emailError && <span className="error">{emailError}</span>}
          </div>
          <div className="form-group">
            <label htmlFor="edit-rol">Rol</label>
            <select
              id="edit-rol"
              value={form.rol_id || ''}
              onChange={(e) => handleChange('rol_id', e.target.value)}
            >
              <option value="">Sin cambiar ({selectedRolName})</option>
              {ROLES.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="edit-estado">Estado actual</label>
            <input id="edit-estado" value={usuario.activo ? 'Activo' : 'Inactivo'} disabled />
          </div>
          {error && <div className="error-banner">{error}</div>}
          <div className="modal-actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Guardando...' : 'Guardar cambios'}
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
