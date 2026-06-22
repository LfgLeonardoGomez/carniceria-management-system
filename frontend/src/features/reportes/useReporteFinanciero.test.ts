/**
 * Tests for useReporteFinanciero hook (Task 7.1 RED + TRIANGULATE).
 *
 * TDD cycle:
 *   7.1 RED — hook fetches /reportes/financieros with group_by + date params;
 *             returns typed rows; null indicators remain null (not coerced to 0)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import type { ReporteFinancieroResponse, GroupBy } from './types'

// ---------------------------------------------------------------------------
// Mock the api module
// ---------------------------------------------------------------------------
vi.mock('./api', () => ({
  fetchReportesVentas: vi.fn(),
  buildExportUrl: vi.fn(),
  fetchReporteFinanciero: vi.fn(),
}))

import * as reportesApi from './api'

const mockResponseWithNulls: ReporteFinancieroResponse = {
  group_by: 'mes',
  rows: [
    {
      periodo: '2026-06',
      ventas: '1000.00',
      gastos: '150.00',
      costos: null,
      utilidad_bruta: null,
      utilidad_neta: null,
    },
  ],
}

const mockResponseFull: ReporteFinancieroResponse = {
  group_by: 'mes',
  rows: [
    {
      periodo: '2026-05',
      ventas: '1000.00',
      gastos: '150.00',
      costos: '600.00',
      utilidad_bruta: '400.00',
      utilidad_neta: '250.00',
    },
  ],
}

// ---------------------------------------------------------------------------
// Task 7.1 RED
// ---------------------------------------------------------------------------

describe('useReporteFinanciero', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('fetches /reportes/financieros with group_by and returns rows', async () => {
    vi.mocked(reportesApi.fetchReporteFinanciero).mockResolvedValue(mockResponseFull)

    const { useReporteFinanciero } = await import('./useReporteFinanciero')
    const { result } = renderHook(() =>
      useReporteFinanciero({
        group_by: 'mes',
        fecha_desde: '2026-05-01T00:00:00Z',
        fecha_hasta: '2026-05-31T23:59:59Z',
      })
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(reportesApi.fetchReporteFinanciero).toHaveBeenCalledWith({
      group_by: 'mes',
      fecha_desde: '2026-05-01T00:00:00Z',
      fecha_hasta: '2026-05-31T23:59:59Z',
    })
    expect(result.current.rows).toHaveLength(1)
    expect(result.current.rows[0].periodo).toBe('2026-05')
    expect(result.current.error).toBeNull()
  })

  it('null indicators remain null — not coerced to 0', async () => {
    vi.mocked(reportesApi.fetchReporteFinanciero).mockResolvedValue(mockResponseWithNulls)

    const { useReporteFinanciero } = await import('./useReporteFinanciero')
    const { result } = renderHook(() =>
      useReporteFinanciero({ group_by: 'mes' })
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    const row = result.current.rows[0]
    expect(row.costos).toBeNull()
    expect(row.utilidad_bruta).toBeNull()
    expect(row.utilidad_neta).toBeNull()
    // ventas and gastos are always present
    expect(row.ventas).toBe('1000.00')
    expect(row.gastos).toBe('150.00')
  })

  it('starts loading and clears error on new params', async () => {
    let resolve: (v: ReporteFinancieroResponse) => void
    const pending = new Promise<ReporteFinancieroResponse>((res) => {
      resolve = res
    })
    vi.mocked(reportesApi.fetchReporteFinanciero).mockReturnValue(pending)

    const { useReporteFinanciero } = await import('./useReporteFinanciero')
    const { result } = renderHook(() =>
      useReporteFinanciero({ group_by: 'dia' })
    )

    expect(result.current.isLoading).toBe(true)

    act(() => resolve!(mockResponseFull))
    await waitFor(() => expect(result.current.isLoading).toBe(false))
  })

  it('returns empty rows list for an empty range (not an error)', async () => {
    vi.mocked(reportesApi.fetchReporteFinanciero).mockResolvedValue({
      group_by: 'mes',
      rows: [],
    })

    const { useReporteFinanciero } = await import('./useReporteFinanciero')
    const { result } = renderHook(() =>
      useReporteFinanciero({ group_by: 'mes' })
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.rows).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('refetches when group_by changes', async () => {
    vi.mocked(reportesApi.fetchReporteFinanciero)
      .mockResolvedValueOnce({ group_by: 'mes', rows: [] })
      .mockResolvedValueOnce({ group_by: 'dia', rows: [] })

    const { useReporteFinanciero } = await import('./useReporteFinanciero')
    let currentGroupBy: GroupBy = 'mes'

    const { result, rerender } = renderHook(() =>
      useReporteFinanciero({ group_by: currentGroupBy })
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(reportesApi.fetchReporteFinanciero).toHaveBeenCalledTimes(1)

    currentGroupBy = 'dia'
    rerender()

    await waitFor(() => expect(reportesApi.fetchReporteFinanciero).toHaveBeenCalledTimes(2))
  })
})
