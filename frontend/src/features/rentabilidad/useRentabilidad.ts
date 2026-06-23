/**
 * Hooks for the rentabilidad feature (C-19).
 *
 * useRentabilidadProductos — fetches GET /rentabilidad/productos
 * useRentabilidadCortes    — fetches GET /rentabilidad/cortes
 *
 * Uses the same useEffect + useState + filtersKey pattern as
 * useReporteFinanciero (C-18). TypeScript strict: no `any`.
 * Null margins are NEVER coerced to zero.
 */
import { useEffect, useState, useRef } from 'react'
import { fetchRentabilidadProductos, fetchRentabilidadCortes } from './api'
import type {
  ProductoRentabilidadRow,
  CorteRentabilidadRow,
  RentabilidadProductosFilters,
  RentabilidadCortesFilters,
} from './types'

// ---------------------------------------------------------------------------
// useRentabilidadProductos
// ---------------------------------------------------------------------------

interface UseRentabilidadProductosResult {
  rows: ProductoRentabilidadRow[]
  isLoading: boolean
  error: Error | null
}

export function useRentabilidadProductos(
  filters: RentabilidadProductosFilters,
): UseRentabilidadProductosResult {
  const [rows, setRows] = useState<ProductoRentabilidadRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  // Stable serialisation for dependency comparison (mirrors useReporteFinanciero)
  const filtersKey = JSON.stringify(filters)
  const filtersRef = useRef(filters)
  filtersRef.current = filters

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetchRentabilidadProductos(filtersRef.current)
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

// ---------------------------------------------------------------------------
// useRentabilidadCortes
// ---------------------------------------------------------------------------

interface UseRentabilidadCortesResult {
  rows: CorteRentabilidadRow[]
  isLoading: boolean
  error: Error | null
}

export function useRentabilidadCortes(
  filters: RentabilidadCortesFilters,
): UseRentabilidadCortesResult {
  const [rows, setRows] = useState<CorteRentabilidadRow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const filtersKey = JSON.stringify(filters)
  const filtersRef = useRef(filters)
  filtersRef.current = filters

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)

    fetchRentabilidadCortes(filtersRef.current)
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
