/**
 * Tests for useRentabilidadProductos and useRentabilidadCortes hooks (Task 7.2).
 *
 * TDD cycle:
 *   7.2 RED — hooks fetch /rentabilidad/{productos,cortes}; null margins stay null;
 *             refetch on filter change; loading state managed correctly.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import type {
  RentabilidadProductosResponse,
  RentabilidadCortesResponse,
  RentabilidadProductosFilters,
} from './types'

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------
vi.mock('./api', () => ({
  fetchRentabilidadProductos: vi.fn(),
  fetchRentabilidadCortes: vi.fn(),
}))

import * as rentabilidadApi from './api'

// ---------------------------------------------------------------------------
// Test data
// ---------------------------------------------------------------------------

const productosFull: RentabilidadProductosResponse = {
  rows: [
    {
      producto_id: 'uuid-1',
      nombre: 'Asado',
      ventas: '1000.00',
      ganancia: '400.00',
      margen_porcentaje: '40.00',
    },
    {
      producto_id: 'uuid-2',
      nombre: 'Molida',
      ventas: '500.00',
      ganancia: null,
      margen_porcentaje: null,
    },
  ],
}

const productosEmpty: RentabilidadProductosResponse = { rows: [] }

const cortesFull: RentabilidadCortesResponse = {
  rows: [
    {
      tipo_corte: 'asado',
      producto_id: 'uuid-1',
      nombre_producto: 'Asado',
      costo_por_kilo: '800.00',
      precio_venta_promedio: '1000.00',
      margen_por_kilo: '200.00',
      margen_porcentaje: '20.00',
    },
  ],
}

const cortesNoSales: RentabilidadCortesResponse = {
  rows: [
    {
      tipo_corte: 'vacio',
      producto_id: 'uuid-3',
      nombre_producto: 'Vacio',
      costo_por_kilo: '900.00',
      precio_venta_promedio: null,
      margen_por_kilo: null,
      margen_porcentaje: null,
    },
  ],
}

// ---------------------------------------------------------------------------
// useRentabilidadProductos tests
// ---------------------------------------------------------------------------

describe('useRentabilidadProductos', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('fetches /rentabilidad/productos and returns rows', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadProductos).mockResolvedValue(productosFull)

    const { useRentabilidadProductos } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadProductos({ orden: 'mayor' })
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(rentabilidadApi.fetchRentabilidadProductos).toHaveBeenCalledWith({ orden: 'mayor' })
    expect(result.current.rows).toHaveLength(2)
    expect(result.current.rows[0].nombre).toBe('Asado')
    expect(result.current.error).toBeNull()
  })

  it('null ganancia and margen_porcentaje stay null — never coerced to 0', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadProductos).mockResolvedValue(productosFull)

    const { useRentabilidadProductos } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadProductos({ orden: 'mayor' })
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    const nullRow = result.current.rows.find((r) => r.nombre === 'Molida')
    expect(nullRow).toBeDefined()
    expect(nullRow!.ganancia).toBeNull()
    expect(nullRow!.margen_porcentaje).toBeNull()
  })

  it('starts with isLoading=true and transitions to false', async () => {
    let resolve: (v: RentabilidadProductosResponse) => void
    const pending = new Promise<RentabilidadProductosResponse>((res) => { resolve = res })
    vi.mocked(rentabilidadApi.fetchRentabilidadProductos).mockReturnValue(pending)

    const { useRentabilidadProductos } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadProductos({ orden: 'mayor' })
    )

    expect(result.current.isLoading).toBe(true)

    act(() => resolve!(productosFull))
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('returns empty rows for empty response (not an error)', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadProductos).mockResolvedValue(productosEmpty)

    const { useRentabilidadProductos } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadProductos({})
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.rows).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('refetches when filters change', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadProductos)
      .mockResolvedValueOnce(productosFull)
      .mockResolvedValueOnce(productosEmpty)

    const { useRentabilidadProductos } = await import('./useRentabilidad')
    let currentFilters: RentabilidadProductosFilters = { orden: 'mayor' }

    const { result, rerender } = renderHook(() =>
      useRentabilidadProductos(currentFilters)
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(rentabilidadApi.fetchRentabilidadProductos).toHaveBeenCalledTimes(1)

    currentFilters = { orden: 'menor' }
    rerender()

    await waitFor(() => expect(rentabilidadApi.fetchRentabilidadProductos).toHaveBeenCalledTimes(2))
  })
})

// ---------------------------------------------------------------------------
// useRentabilidadCortes tests
// ---------------------------------------------------------------------------

describe('useRentabilidadCortes', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('fetches /rentabilidad/cortes and returns rows', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadCortes).mockResolvedValue(cortesFull)

    const { useRentabilidadCortes } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadCortes({})
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(rentabilidadApi.fetchRentabilidadCortes).toHaveBeenCalledWith({})
    expect(result.current.rows).toHaveLength(1)
    expect(result.current.rows[0].tipo_corte).toBe('asado')
    expect(result.current.error).toBeNull()
  })

  it('null margin fields stay null when no sales in range', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadCortes).mockResolvedValue(cortesNoSales)

    const { useRentabilidadCortes } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadCortes({})
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    const row = result.current.rows[0]
    expect(row.precio_venta_promedio).toBeNull()
    expect(row.margen_por_kilo).toBeNull()
    expect(row.margen_porcentaje).toBeNull()
    // costo_por_kilo always present
    expect(row.costo_por_kilo).toBe('900.00')
  })

  it('propagates fetch error into error state', async () => {
    const err = new Error('Network error')
    vi.mocked(rentabilidadApi.fetchRentabilidadCortes).mockRejectedValue(err)

    const { useRentabilidadCortes } = await import('./useRentabilidad')
    const { result } = renderHook(() =>
      useRentabilidadCortes({})
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.error).toBeInstanceOf(Error)
    expect(result.current.error?.message).toBe('Network error')
    expect(result.current.rows).toEqual([])
  })

  it('refetches when date filters change', async () => {
    vi.mocked(rentabilidadApi.fetchRentabilidadCortes)
      .mockResolvedValueOnce(cortesFull)
      .mockResolvedValueOnce({ rows: [] })

    const { useRentabilidadCortes } = await import('./useRentabilidad')
    let filters = {}

    const { result, rerender } = renderHook(() =>
      useRentabilidadCortes(filters)
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(rentabilidadApi.fetchRentabilidadCortes).toHaveBeenCalledTimes(1)

    filters = { fecha_desde: '2026-06-01T00:00:00Z' }
    rerender()

    await waitFor(() => expect(rentabilidadApi.fetchRentabilidadCortes).toHaveBeenCalledTimes(2))
  })
})
