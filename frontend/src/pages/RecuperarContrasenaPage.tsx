import { useState } from 'react'
import { Link } from 'react-router-dom'
import { recover } from '@/features/auth/api'

export function RecuperarContrasenaPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  function isValidEmail(value: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (!isValidEmail(email)) {
      setError('Ingresá un email válido.')
      return
    }

    setLoading(true)
    try {
      await recover({ email })
      setSuccess(true)
      setEmail('')
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Error al procesar la solicitud. Intentá de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Recuperar contraseña</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        {error && <div role="alert">{error}</div>}
        {success && (
          <div role="status">
            Si el email existe en nuestro sistema, recibirás instrucciones para recuperar tu contraseña. Revisá tu correo.
          </div>
        )}
        <button type="submit" disabled={loading}>
          {loading ? 'Enviando...' : 'Enviar instrucciones'}
        </button>
      </form>
      <Link to="/login">Volver al login</Link>
    </div>
  )
}
