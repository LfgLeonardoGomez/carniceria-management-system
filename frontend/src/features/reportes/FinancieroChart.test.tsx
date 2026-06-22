/**
 * Tests for FinancieroChart component (Task 8.3 RED).
 *
 * TDD cycle:
 *   8.3 RED — renders chart rows for each period; no external charting lib
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { FinancieroPeriodoRow } from './types'

const rows: FinancieroPeriodoRow[] = [
  {
    periodo: '2026-06',
    ventas: '1000.00',
    gastos: '150.00',
    costos: '600.00',
    utilidad_bruta: '400.00',
    utilidad_neta: '250.00',
  },
  {
    periodo: '2026-07',
    ventas: '1500.00',
    gastos: '200.00',
    costos: null,
    utilidad_bruta: null,
    utilidad_neta: null,
  },
]

describe('FinancieroChart', () => {
  it('renders a chart container', async () => {
    const { FinancieroChart } = await import('./FinancieroChart')
    render(<FinancieroChart rows={rows} />)

    expect(screen.getByTestId('financiero-chart')).toBeInTheDocument()
  })

  it('renders one bar group per period', async () => {
    const { FinancieroChart } = await import('./FinancieroChart')
    render(<FinancieroChart rows={rows} />)

    const barGroups = screen.getAllByTestId('chart-bar-group')
    expect(barGroups).toHaveLength(2)
  })

  it('shows periodo labels in chart', async () => {
    const { FinancieroChart } = await import('./FinancieroChart')
    render(<FinancieroChart rows={rows} />)

    expect(screen.getByText('2026-06')).toBeInTheDocument()
    expect(screen.getByText('2026-07')).toBeInTheDocument()
  })

  it('renders empty state when no rows', async () => {
    const { FinancieroChart } = await import('./FinancieroChart')
    render(<FinancieroChart rows={[]} />)

    expect(screen.getByTestId('chart-empty')).toBeInTheDocument()
  })

  it('renders null cost bars gracefully (no crash)', async () => {
    const { FinancieroChart } = await import('./FinancieroChart')
    // Should not throw when a row has null indicators
    expect(() => render(<FinancieroChart rows={rows} />)).not.toThrow()
  })
})
