/**
 * Hook for the financial report — fetches GET /reportes/financieros.
 *
 * Uses the same useEffect + useState pattern as useReportesVentas (C-17).
 * TypeScript strict: no `any`. Null indicators stay null — never coerced to 0.
 *
 * C-18, Task 7.2 GREEN.
 */
import { useEffect, useState, useRef } from 'react'
import { fetchReporteFinanciero } from './api'
import type { FinancieroPeriodoRow, ReporteFinancieroFilters } from './types'

interface UseReporteFinancieroResult {
  rows: FinancieroPeriodoRow[]
  isLoading: boolean
  error: Error | null
}

export function useReporteFinanciero(
  filters: ReporteFinancieroFilters,
): UseReporteFinancieroResult {
  const [rows, setRows] = useState<FinancieroPeriodoRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // Stable serialisation for dependency comparison (matches useReportesVentas pattern)
  const filtersKey = JSON.stringify(filters)
  const filtersRef = useRef(filters)
  filtersRef.current = filters

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetchReporteFinanciero(filtersRef.current)
      .then((data) => {
        if (!cancelled) {
          setRows(data.rows)
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

  return { rows, isLoading, error }
}
