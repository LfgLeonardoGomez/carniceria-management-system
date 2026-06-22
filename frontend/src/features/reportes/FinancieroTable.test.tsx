/**
 * Tests for FinancieroTable component (Task 8.1 RED + TRIANGULATE).
 *
 * TDD cycle:
 *   8.1 RED — renders one row per period; null costos → "no disponible" (not "0")
 *   8.6 TRIANGULATE — changing group_by refetches; money formatting
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { FinancieroPeriodoRow } from './types'

const rowWithNulls: FinancieroPeriodoRow = {
  periodo: '2026-06',
  ventas: '1000.00',
  gastos: '150.00',
  costos: null,
  utilidad_bruta: null,
  utilidad_neta: null,
}

const rowFull: FinancieroPeriodoRow = {
  periodo: '2026-07',
  ventas: '2000.00',
  gastos: '300.00',
  costos: '1200.00',
  utilidad_bruta: '800.00',
  utilidad_neta: '500.00',
}

describe('FinancieroTable', () => {
  it('renders one row per period', async () => {
    const { FinancieroTable } = await import('./FinancieroTable')
    render(<FinancieroTable rows={[rowWithNulls, rowFull]} />)

    // Two data rows (one per period)
    const periodoEls = screen.getAllByTestId('financiero-periodo')
    expect(periodoEls).toHaveLength(2)
    expect(periodoEls[0]).toHaveTextContent('2026-06')
    expect(periodoEls[1]).toHaveTextContent('2026-07')
  })

  it('renders null costos as "no disponible", not "0"', async () => {
    const { FinancieroTable } = await import('./FinancieroTable')
    render(<FinancieroTable rows={[rowWithNulls]} />)

    // costos, utilidad_bruta, utilidad_neta cells for the null row
    const costosCells = screen.getAllByTestId('financiero-costos')
    expect(costosCells[0]).toHaveTextContent('no disponible')
    expect(costosCells[0]).not.toHaveTextContent('0')

    const brutaCells = screen.getAllByTestId('financiero-utilidad-bruta')
    expect(brutaCells[0]).toHaveTextContent('no disponible')

    const netaCells = screen.getAllByTestId('financiero-utilidad-neta')
    expect(netaCells[0]).toHaveTextContent('no disponible')
  })

  it('renders actual Decimal values when cost snapshot is available', async () => {
    const { FinancieroTable } = await import('./FinancieroTable')
    render(<FinancieroTable rows={[rowFull]} />)

    const costosCells = screen.getAllByTestId('financiero-costos')
    expect(costosCells[0]).not.toHaveTextContent('no disponible')
    // The value 1200.00 should appear somewhere in the cell
    expect(costosCells[0].textContent).toMatch(/1200|1\.200/)
  })

  it('renders ventas and gastos which are always present', async () => {
    const { FinancieroTable } = await import('./FinancieroTable')
    render(<FinancieroTable rows={[rowWithNulls]} />)

    const ventasCells = screen.getAllByTestId('financiero-ventas')
    expect(ventasCells[0]).not.toHaveTextContent('no disponible')

    const gastosCells = screen.getAllByTestId('financiero-gastos')
    expect(gastosCells[0]).not.toHaveTextContent('no disponible')
  })

  it('renders empty state when rows is empty', async () => {
    const { FinancieroTable } = await import('./FinancieroTable')
    render(<FinancieroTable rows={[]} />)

    expect(screen.getByTestId('financiero-empty')).toBeInTheDocument()
  })
})
