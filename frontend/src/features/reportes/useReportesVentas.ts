/**
 * Hook for the sales report — fetches GET /reportes/ventas.
 *
 * Uses the same useEffect + useState pattern as the rest of the project
 * (no external query library is installed). TypeScript strict: no `any`.
 */
import { useEffect, useState, useRef } from 'react'
import { fetchReportesVentas } from './api'
import type { ReportesFilters, VentaReporteRow } from './types'

interface UseReportesVentasResult {
  rows: VentaReporteRow[]
  total: number
  isLoading: boolean
  error: Error | null
}

export function useReportesVentas(filters: ReportesFilters): UseReportesVentasResult {
  const [rows, setRows] = useState<VentaReporteRow[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // Stable serialisation for dependency comparison
  const filtersKey = JSON.stringify(filters)
  // Use a ref so the effect can read the latest value without re-triggering
  const filtersRef = useRef(filters)
  filtersRef.current = filters

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetchReportesVentas(filtersRef.current)
      .then((data) => {
        if (!cancelled) {
          setRows(data.rows)
          setTotal(data.total)
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
  }, [filtersKey])

  return { rows, total, isLoading, error }
}
