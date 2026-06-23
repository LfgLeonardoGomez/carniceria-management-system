/**
 * PagoForm — payment registration form (C-14, Task 6.5).
 *
 * Props:
 *   clienteId  — customer UUID string
 *   onSuccess  — called with the new saldo_actual after a successful payment
 *
 * Client-side validation: importe must be a number > 0.
 * Surfaces 409 overpayment and other API errors in a visible error element.
 * TypeScript strict: no `any`.
 */
import { useState } from 'react'
import { registrarPago } from './api'

interface PagoFormProps {
  clienteId: string
  onSuccess: (nuevoSaldo: string) => void
}

function extractErrorMessage(err: unknown): string {
  // Axios error with response
  if (
    err !== null &&
    typeof err === 'object' &&
    'response' in err &&
    err.response !== null &&
    typeof err.response === 'object' &&
    'data' in err.response
  ) {
    const data = (err.response as { data: unknown }).data
    if (data !== null && typeof data === 'object' && 'detail' in data) {
      return String((data as { detail: unknown }).detail)
    }
    const status = 'status' in err.response ? (err.response as { status: number }).status : undefined
    if (status === 409) {
      return 'El importe supera el saldo actual. No se permiten pagos en exceso.'
    }
  }
  if (err instanceof Error) return err.message
  return 'Error al registrar el pago. Intente nuevamente.'
}

export function PagoForm({ clienteId, onSuccess }: PagoFormProps): JSX.Element {
  const [importe, setImporte] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successSaldo, setSuccessSaldo] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessSaldo(null)

    const parsed = parseFloat(importe)
    if (isNaN(parsed) || parsed <= 0) {
      setError('El importe debe ser un valor positivo mayor a cero.')
      return
    }

    // Format to 2 decimal places to send as string
    const importeStr = parsed.toFixed(2)

    setIsSubmitting(true)
    try {
      const result = await registrarPago(clienteId, { importe: importeStr })
      setSuccessSaldo(result.saldo_actual)
      setImporte('')
      onSuccess(result.saldo_actual)
    } catch (err: unknown) {
      setError(extractErrorMessage(err))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} data-testid="pago-form">
      <div>
        <label htmlFor="pago-importe">Importe</label>
        <input
          id="pago-importe"
          type="number"
          step="0.01"
          value={importe}
          onChange={(e) => setImporte(e.target.value)}
          placeholder="0.00"
          disabled={isSubmitting}
          data-testid="pago-importe-input"
        />
      </div>

      {error && (
        <p data-testid="pago-error" style={{ color: 'red' }}>
          {error}
        </p>
      )}

      {successSaldo !== null && (
        <p data-testid="pago-success-saldo">
          Pago registrado. Nuevo saldo: {successSaldo}
        </p>
      )}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Registrando...' : 'Registrar pago'}
      </button>
    </form>
  )
}
