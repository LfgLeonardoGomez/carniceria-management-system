import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useUsuarioStore } from '@/stores/usuarioStore'

export function PerfilPage() {
  const navigate = useNavigate()
  const { user, isAuthenticated, setUser } = useAuthStore()
  const { perfil, loading, error, fetchPerfil, updatePerfil, changePassword, clearError } = useUsuarioStore()

  const [form, setForm] = useState({
    nombre: '',
    apellido: '',
    email: '',
  })

  const [passwordForm, setPasswordForm] = useState({
    contrasena_actual: '',
    contrasena_nueva: '',
    confirmacion: '',
  })
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [profileSuccess, setProfileSuccess] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    fetchPerfil().catch(() => {})
  }, [isAuthenticated, navigate, fetchPerfil])

  useEffect(() => {
    if (perfil) {
      setForm({
        nombre: perfil.nombre || '',
        apellido: perfil.apellido || '',
        email: perfil.email || '',
      })
    }
  }, [perfil])

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => clearError(), 8000)
      return () => clearTimeout(timer)
    }
  }, [error, clearError])

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    try {
      await updatePerfil(form)
      setProfileSuccess(true)
      setTimeout(() => setProfileSuccess(false), 4000)
      // Sync auth store if email changed
      if (user && form.email !== user.email) {
        setUser({ ...user, email: form.email, nombre: form.nombre, apellido: form.apellido })
      }
    } catch {
      // error ya está en el store
    }
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(false)

    if (passwordForm.contrasena_nueva.length < 6) {
      setPasswordError('La contraseña nueva debe tener al menos 6 caracteres')
      return
    }
    if (passwordForm.contrasena_nueva !== passwordForm.confirmacion) {
      setPasswordError('Las contraseñas no coinciden')
      return
    }

    try {
      await changePassword({
        contrasena_actual: passwordForm.contrasena_actual,
        contrasena_nueva: passwordForm.contrasena_nueva,
      })
      setPasswordSuccess(true)
      setPasswordForm({ contrasena_actual: '', contrasena_nueva: '', confirmacion: '' })
      setTimeout(() => setPasswordSuccess(false), 4000)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setPasswordError(axiosErr.response?.data?.detail || 'Error al cambiar contraseña')
    }
  }

  return (
    <div className="perfil-page">
      <h1>Mi perfil</h1>
      {error && <div className="error-banner" role="alert">{error}</div>}
      {profileSuccess && (
        <div className="success-banner" role="status">
          Perfil actualizado correctamente
        </div>
      )}

      <form onSubmit={handleProfileSubmit} className="perfil-form">
        <h2>Datos personales</h2>
        <div className="form-group">
          <label htmlFor="perfil-nombre">Nombre</label>
          <input
            id="perfil-nombre"
            value={form.nombre}
            onChange={(e) => setForm({ ...form, nombre: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label htmlFor="perfil-apellido">Apellido</label>
          <input
            id="perfil-apellido"
            value={form.apellido}
            onChange={(e) => setForm({ ...form, apellido: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label htmlFor="perfil-email">Email</label>
          <input
            id="perfil-email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div className="form-group">
          <label>Rol</label>
          <input value={user?.rol || ''} disabled />
        </div>
        <div className="form-group">
          <label>Empresa</label>
          <input value={perfil?.empresa || ''} disabled />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </form>

      <form onSubmit={handlePasswordSubmit} className="password-form">
        <h2>Cambiar contraseña</h2>
        {passwordError && <div className="error-banner" role="alert">{passwordError}</div>}
        {passwordSuccess && (
          <div className="success-banner" role="status">
            Contraseña actualizada correctamente
          </div>
        )}
        <div className="form-group">
          <label htmlFor="pass-actual">Contraseña actual</label>
          <input
            id="pass-actual"
            type="password"
            value={passwordForm.contrasena_actual}
            onChange={(e) => setPasswordForm({ ...passwordForm, contrasena_actual: e.target.value })}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="pass-nueva">Contraseña nueva</label>
          <input
            id="pass-nueva"
            type="password"
            value={passwordForm.contrasena_nueva}
            onChange={(e) => setPasswordForm({ ...passwordForm, contrasena_nueva: e.target.value })}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="pass-confirm">Confirmar contraseña nueva</label>
          <input
            id="pass-confirm"
            type="password"
            value={passwordForm.confirmacion}
            onChange={(e) => setPasswordForm({ ...passwordForm, confirmacion: e.target.value })}
            required
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Cambiando...' : 'Cambiar contraseña'}
        </button>
      </form>
    </div>
  )
}
