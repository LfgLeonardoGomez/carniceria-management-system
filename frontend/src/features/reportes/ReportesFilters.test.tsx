/**
 * Tests for ReportesFilters component.
 *
 * TDD cycle: RED → GREEN → TRIANGULATE
 * Tasks:
 *   8.1 — date range inputs and cliente selector render;
 *          clicking Apply calls onFilter with correct values;
 *          "All clients" option clears cliente_id
 *   8.3 — submitting with no dates calls onFilter with fecha_desde: undefined,
 *          fecha_hasta: undefined (not empty string)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import type { ReportesFilters } from './types'

// ---------------------------------------------------------------------------
// Mock the clientes API so component renders without HTTP calls
// ---------------------------------------------------------------------------
vi.mock('@/features/clientes/api', () => ({
  fetchClientes: vi.fn().mockResolvedValue({
    items: [
      { id: 'c1', nombre: 'Juan', apellido: 'Perez', razon_social: null },
      { id: 'c2', nombre: 'Maria', apellido: 'Lopez', razon_social: 'Supermercado SA' },
    ],
    total: 2,
  }),
}))

// ---------------------------------------------------------------------------
// Task 8.1 — date range inputs and cliente selector render
// ---------------------------------------------------------------------------

describe('ReportesFilters', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders date range inputs and cliente selector', async () => {
    const { ReportesFilters } = await import('./ReportesFilters')
    const onFilter = vi.fn()

    render(<ReportesFilters onFilter={onFilter} />)

    expect(screen.getByLabelText(/fecha desde/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/fecha hasta/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /cliente/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /aplicar|apply/i })).toBeInTheDocument()
  })

  it('calls onFilter with correct values when Apply is clicked with dates', async () => {
    const { ReportesFilters } = await import('./ReportesFilters')
    const onFilter = vi.fn()

    render(<ReportesFilters onFilter={onFilter} />)

    fireEvent.change(screen.getByLabelText(/fecha desde/i), {
      target: { value: '2024-06-01' },
    })
    fireEvent.change(screen.getByLabelText(/fecha hasta/i), {
      target: { value: '2024-06-30' },
    })
    fireEvent.click(screen.getByRole('button', { name: /aplicar|apply/i }))

    expect(onFilter).toHaveBeenCalledTimes(1)
    const calledWith: ReportesFilters = onFilter.mock.calls[0][0]
    expect(calledWith.fecha_desde).toBeDefined()
    expect(calledWith.fecha_hasta).toBeDefined()
    expect(calledWith.fecha_desde).toContain('2024-06-01')
    expect(calledWith.fecha_hasta).toContain('2024-06-30')
  })

  it('clears cliente_id when "All clients" option is selected', async () => {
    const { ReportesFilters } = await import('./ReportesFilters')
    const onFilter = vi.fn()

    render(<ReportesFilters onFilter={onFilter} />)

    const select = screen.getByRole('combobox', { name: /cliente/i })
    // Select "All clients" (empty value)
    fireEvent.change(select, { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: /aplicar|apply/i }))

    const calledWith: ReportesFilters = onFilter.mock.calls[0][0]
    expect(calledWith.cliente_id).toBeUndefined()
  })

  // ---------------------------------------------------------------------------
  // Task 8.3 — TRIANGULATE: submitting with no dates → undefined (not empty string)
  // ---------------------------------------------------------------------------

  it('calls onFilter with fecha_desde/hasta undefined when no dates entered', async () => {
    const { ReportesFilters } = await import('./ReportesFilters')
    const onFilter = vi.fn()

    render(<ReportesFilters onFilter={onFilter} />)

    // Do not fill any date fields — just click apply
    fireEvent.click(screen.getByRole('button', { name: /aplicar|apply/i }))

    expect(onFilter).toHaveBeenCalledTimes(1)
    const calledWith: ReportesFilters = onFilter.mock.calls[0][0]
    expect(calledWith.fecha_desde).toBeUndefined()
    expect(calledWith.fecha_hasta).toBeUndefined()
  })
})
