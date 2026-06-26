import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { reset } from '@/features/auth/api'

export function RestablecerContrasenaPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const navigate = useNavigate()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }

    if (!token) {
      setError('El enlace es inválido o incompleto.')
      return
    }

    setLoading(true)
    try {
      await reset({ token, new_password: password })
      navigate('/login')
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Error al restablecer la contraseña. Intentá de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div>
        <h1>Restablecer contraseña</h1>
        <div role="alert">El enlace es inválido o incompleto.</div>
        <Link to="/recuperar-contrasena">Solicitar un nuevo enlace</Link>
      </div>
    )
  }

  return (
    <div>
      <h1>Restablecer contraseña</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="password">Nueva contraseña</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="confirmPassword">Confirmar contraseña</label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        {error && (
          <div role="alert">
            {error}
            {error.includes('inválido') || error.includes('expirado') ? (
              <div>
                <Link to="/recuperar-contrasena">Solicitar un nuevo enlace</Link>
              </div>
            ) : null}
          </div>
        )}
        <button type="submit" disabled={loading}>
          {loading ? 'Restableciendo...' : 'Restablecer contraseña'}
        </button>
      </form>
    </div>
  )
}
