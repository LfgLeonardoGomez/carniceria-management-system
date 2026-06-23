/**
 * Tests for RentabilidadFilters (Task 8.3).
 *
 * TDD cycle:
 *   RED — renders date-from and date-to inputs; calls onChange on change
 *   TRIANGULATE — both inputs present; undefined values render as empty
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

describe('RentabilidadFilters', () => {
  it('renders fecha_desde and fecha_hasta inputs', async () => {
    const { RentabilidadFilters } = await import('./RentabilidadFilters')
    render(
      <RentabilidadFilters
        fechaDesde={undefined}
        fechaHasta={undefined}
        onFechaDesdeChange={() => undefined}
        onFechaHastaChange={() => undefined}
      />
    )

    expect(screen.getByTestId('filter-fecha-desde')).toBeInTheDocument()
    expect(screen.getByTestId('filter-fecha-hasta')).toBeInTheDocument()
  })

  it('calls onFechaDesdeChange when fecha_desde input changes', async () => {
    const { RentabilidadFilters } = await import('./RentabilidadFilters')
    const handler = vi.fn()
    render(
      <RentabilidadFilters
        fechaDesde={undefined}
        fechaHasta={undefined}
        onFechaDesdeChange={handler}
        onFechaHastaChange={() => undefined}
      />
    )

    const input = screen.getByTestId('filter-fecha-desde')
    fireEvent.change(input, { target: { value: '2026-06-01' } })
    expect(handler).toHaveBeenCalled()
  })

  it('calls onFechaHastaChange when fecha_hasta input changes', async () => {
    const { RentabilidadFilters } = await import('./RentabilidadFilters')
    const handler = vi.fn()
    render(
      <RentabilidadFilters
        fechaDesde={undefined}
        fechaHasta={undefined}
        onFechaDesdeChange={() => undefined}
        onFechaHastaChange={handler}
      />
    )

    const input = screen.getByTestId('filter-fecha-hasta')
    fireEvent.change(input, { target: { value: '2026-06-30' } })
    expect(handler).toHaveBeenCalled()
  })

  it('pre-fills inputs with provided values', async () => {
    const { RentabilidadFilters } = await import('./RentabilidadFilters')
    render(
      <RentabilidadFilters
        fechaDesde="2026-06-01"
        fechaHasta="2026-06-30"
        onFechaDesdeChange={() => undefined}
        onFechaHastaChange={() => undefined}
      />
    )

    const desdeInput = screen.getByTestId('filter-fecha-desde') as HTMLInputElement
    const hastaInput = screen.getByTestId('filter-fecha-hasta') as HTMLInputElement
    expect(desdeInput.value).toBe('2026-06-01')
    expect(hastaInput.value).toBe('2026-06-30')
  })
})
