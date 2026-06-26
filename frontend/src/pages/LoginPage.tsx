import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '@/features/auth/api'
import { useAuthStore } from '@/store/authStore'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setToken, setUser } = useAuthStore()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const data = await login({ email, contrasena: password })
      localStorage.setItem('access_token', data.access_token)
      setToken(data.access_token)
      setUser(data.usuario)
      navigate('/')
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      let errorMsg = 'Error al iniciar sesión. Intentá de nuevo.'
      if (typeof detail === 'string') {
        errorMsg = detail
      } else if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: string }
        errorMsg = first?.msg ?? errorMsg
      }
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Iniciar sesión</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <div role="alert">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Ingresando...' : 'Iniciar sesión'}
        </button>
      </form>
      <Link to="/recuperar-contrasena">¿Olvidaste tu contraseña?</Link>
    </div>
  )
}
