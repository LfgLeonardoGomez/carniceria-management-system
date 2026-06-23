/**
 * Hooks for the cuentas-corrientes feature (C-14).
 *
 * useHistorialCC    — fetches movement history + balance for a customer
 * useRegistrarPago  — mutation: register a payment
 *
 * Pattern mirrors useRentabilidadProductos (C-19).
 * TypeScript strict: no `any`.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { descargarEstadoCuenta, fetchHistorialCC, registrarPago } from './api'
import type {
  ExportFormato,
  HistorialCCResponse,
  PagoCreate,
  PagoResponse,
} from './types'

// ---------------------------------------------------------------------------
// useHistorialCC
// ---------------------------------------------------------------------------

interface UseHistorialCCResult {
  historial: HistorialCCResponse | null
  isLoading: boolean
  error: Error | null
  refetch: () => void
}

export function useHistorialCC(
  clienteId: string | null | undefined,
  skip = 0,
  limit = 50,
): UseHistorialCCResult {
  const [historial, setHistorial] = useState<HistorialCCResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [tick, setTick] = useState(0)

  const paramsKey = JSON.stringify({ clienteId, skip, limit, tick })
  const paramsRef = useRef({ clienteId, skip, limit })
  paramsRef.current = { clienteId, skip, limit }

  useEffect(() => {
    if (!paramsRef.current.clienteId) return

    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetchHistorialCC(
      paramsRef.current.clienteId,
      paramsRef.current.skip,
      paramsRef.current.limit,
    )
      .then((data) => {
        if (!cancelled) {
          setHistorial(data)
          setIsLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey])

  const refetch = useCallback(() => setTick((t) => t + 1), [])

  return { historial, isLoading, error, refetch }
}

// ---------------------------------------------------------------------------
// useRegistrarPago
// ---------------------------------------------------------------------------

interface UseRegistrarPagoResult {
  isSubmitting: boolean
  error: Error | null
  result: PagoResponse | null
  registrar: (clienteId: string, data: PagoCreate) => Promise<PagoResponse | null>
}

export function useRegistrarPago(): UseRegistrarPagoResult {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [result, setResult] = useState<PagoResponse | null>(null)

  const registrar = useCallback(
    async (clienteId: string, data: PagoCreate): Promise<PagoResponse | null> => {
      setIsSubmitting(true)
      setError(null)
      try {
        const resp = await registrarPago(clienteId, data)
        setResult(resp)
        setIsSubmitting(false)
        return resp
      } catch (err: unknown) {
        setError(err instanceof Error ? err : new Error(String(err)))
        setIsSubmitting(false)
        return null
      }
    },
    [],
  )

  return { isSubmitting, error, result, registrar }
}

// ---------------------------------------------------------------------------
// useDescargarEstadoCuenta
// ---------------------------------------------------------------------------

interface UseDescargarEstadoCuentaResult {
  isDownloading: boolean
  error: Error | null
  descargar: (clienteId: string, formato: ExportFormato) => Promise<void>
}

export function useDescargarEstadoCuenta(): UseDescargarEstadoCuentaResult {
  const [isDownloading, setIsDownloading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const descargar = useCallback(
    async (clienteId: string, formato: ExportFormato): Promise<void> => {
      setIsDownloading(true)
      setError(null)
      try {
        const blob = await descargarEstadoCuenta(clienteId, formato)
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `estado-cuenta-${clienteId}.${formato}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        setIsDownloading(false)
      } catch (err: unknown) {
        setError(err instanceof Error ? err : new Error(String(err)))
        setIsDownloading(false)
      }
    },
    [],
  )

  return { isDownloading, error, descargar }
}
