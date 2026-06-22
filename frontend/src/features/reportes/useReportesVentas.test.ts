/**
 * Tests for useReportesVentas hook.
 *
 * TDD cycle: RED → GREEN → TRIANGULATE
 * Tasks:
 *   7.1 — hook calls GET /reportes/ventas with correct filter params;
 *          returns rows, total, isLoading, error
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import type { ReportesFilters, ReporteVentasResponse } from './types'

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------
vi.mock('./api', () => ({
  fetchReportesVentas: vi.fn(),
  buildExportUrl: vi.fn(),
}))

import * as reportesApi from './api'

const mockResponse: ReporteVentasResponse = {
  rows: [
    {
      venta_id: '11111111-1111-1111-1111-111111111111',
      fecha: '2024-06-01T10:00:00Z',
      cliente_nombre: 'Juan Perez',
      productos: 'Asado',
      total_kilos: '2.000',
      subtotal: '2000.00',
      total: '2000.00',
      medios_pago: 'efectivo',
      ganancia_estimada: '500.00',
    },
  ],
  total: 1,
  skip: 0,
  limit: 50,
}

// ---------------------------------------------------------------------------
// Task 7.1 — hook calls API with correct params; returns rows/total/isLoading/error
// ---------------------------------------------------------------------------

describe('useReportesVentas', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('calls fetchReportesVentas with correct filter params and returns rows + total', async () => {
    vi.mocked(reportesApi.fetchReportesVentas).mockResolvedValue(mockResponse)

    const { useReportesVentas } = await import('./useReportesVentas')
    const filters: ReportesFilters = {
      fecha_desde: '2024-06-01T00:00:00Z',
      fecha_hasta: '2024-06-30T23:59:59Z',
    }

    const { result } = renderHook(() => useReportesVentas(filters))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(reportesApi.fetchReportesVentas).toHaveBeenCalledWith(filters)
    expect(result.current.rows).toHaveLength(1)
    expect(result.current.total).toBe(1)
    expect(result.current.error).toBeNull()
  })

  it('returns isLoading true initially', async () => {
    // Return a pending promise so we can inspect the loading state
    let resolve: (value: ReporteVentasResponse) => void
    const pending = new Promise<ReporteVentasResponse>((res) => {
      resolve = res
    })
    vi.mocked(reportesApi.fetchReportesVentas).mockReturnValue(pending)

    const { useReportesVentas } = await import('./useReportesVentas')

    const { result } = renderHook(() => useReportesVentas({}))

    // Still loading at this point
    expect(result.current.isLoading).toBe(true)

    // Resolve and clean up
    act(() => resolve!({ rows: [], total: 0, skip: 0, limit: 50 }))
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('calls API with empty filters when no filters provided and returns empty rows', async () => {
    vi.mocked(reportesApi.fetchReportesVentas).mockResolvedValue({
      rows: [],
      total: 0,
      skip: 0,
      limit: 50,
    })

    const { useReportesVentas } = await import('./useReportesVentas')

    const { result } = renderHook(() => useReportesVentas({}))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(reportesApi.fetchReportesVentas).toHaveBeenCalledWith({})
    expect(result.current.rows).toEqual([])
    expect(result.current.total).toBe(0)
  })
})
