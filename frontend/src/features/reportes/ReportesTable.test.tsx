/**
 * Tests for ReportesTable component.
 *
 * TDD cycle: RED → GREEN → TRIANGULATE
 * Tasks:
 *   9.1 — rows render with correct columns; null ganancia displays '—';
 *          empty state displays "No results"; export buttons disabled when rows empty
 *   9.3 — export button href includes correct formato param and current filter params
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type { VentaReporteRow, ReportesFilters } from './types'

// Mock api so buildExportUrl can be controlled
vi.mock('./api', () => ({
  fetchReportesVentas: vi.fn(),
  buildExportUrl: vi.fn((formato: string, filters: ReportesFilters) => {
    const base = `http://localhost:8000/reportes/ventas/exportar?formato=${formato}`
    const parts: string[] = [base]
    if (filters.fecha_desde) parts.push(`fecha_desde=${filters.fecha_desde}`)
    if (filters.fecha_hasta) parts.push(`fecha_hasta=${filters.fecha_hasta}`)
    if (filters.cliente_id) parts.push(`cliente_id=${filters.cliente_id}`)
    return parts.join('&')
  }),
}))

const mockRow: VentaReporteRow = {
  venta_id: '11111111-1111-1111-1111-111111111111',
  fecha: '2024-06-01T10:00:00Z',
  cliente_nombre: 'Juan Perez',
  productos: 'Asado, Vacío',
  total_kilos: '3.500',
  subtotal: '3500.00',
  total: '3500.00',
  medios_pago: 'efectivo',
  ganancia_estimada: '700.00',
}

const mockRowNullGanancia: VentaReporteRow = {
  ...mockRow,
  venta_id: '22222222-2222-2222-2222-222222222222',
  ganancia_estimada: null,
}

// ---------------------------------------------------------------------------
// Task 9.1 — rows render, null ganancia → '—', empty state, disabled buttons
// ---------------------------------------------------------------------------

describe('ReportesTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('renders rows with correct column data', async () => {
    const { ReportesTable } = await import('./ReportesTable')

    render(<ReportesTable rows={[mockRow]} filters={{}} />)

    expect(screen.getByText('Juan Perez')).toBeInTheDocument()
    expect(screen.getByText('Asado, Vacío')).toBeInTheDocument()
    expect(screen.getByText('3.500')).toBeInTheDocument()
    // subtotal and total have the same value in this fixture — use getAllByText
    expect(screen.getAllByText('3500.00').length).toBeGreaterThan(0)
    expect(screen.getByText('efectivo')).toBeInTheDocument()
    expect(screen.getByText('700.00')).toBeInTheDocument()
  })

  it('displays em-dash when ganancia_estimada is null', async () => {
    const { ReportesTable } = await import('./ReportesTable')

    render(<ReportesTable rows={[mockRowNullGanancia]} filters={{}} />)

    // There should be an em-dash for the null ganancia cell
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('displays empty state message when rows is empty', async () => {
    const { ReportesTable } = await import('./ReportesTable')

    render(<ReportesTable rows={[]} filters={{}} />)

    expect(screen.getByText(/sin resultados|no results|no hay resultados/i)).toBeInTheDocument()
  })

  it('export buttons are disabled when rows is empty', async () => {
    const { ReportesTable } = await import('./ReportesTable')

    render(<ReportesTable rows={[]} filters={{}} />)

    const exportButtons = screen.getAllByRole('button').filter(
      (btn) => btn.textContent?.match(/excel|pdf|csv/i),
    )
    expect(exportButtons.length).toBeGreaterThan(0)
    exportButtons.forEach((btn) => {
      expect(btn).toBeDisabled()
    })
  })

  it('export buttons are enabled when rows are present', async () => {
    const { ReportesTable } = await import('./ReportesTable')

    render(<ReportesTable rows={[mockRow]} filters={{}} />)

    const exportButtons = screen.getAllByRole('button').filter(
      (btn) => btn.textContent?.match(/excel|pdf|csv/i),
    )
    expect(exportButtons.length).toBeGreaterThan(0)
    exportButtons.forEach((btn) => {
      expect(btn).not.toBeDisabled()
    })
  })

  // ---------------------------------------------------------------------------
  // Task 9.3 — TRIANGULATE: export button href includes correct formato + filter params
  // ---------------------------------------------------------------------------

  it('export xlsx button includes formato=xlsx and date filter params in URL when clicked', async () => {
    const { ReportesTable } = await import('./ReportesTable')
    const filters: ReportesFilters = {
      fecha_desde: '2024-06-01T00:00:00Z',
      fecha_hasta: '2024-06-30T23:59:59Z',
    }

    const { buildExportUrl } = await import('./api')
    const { fireEvent } = await import('@testing-library/react')

    render(<ReportesTable rows={[mockRow]} filters={filters} />)

    const xlsxButton = screen.getByRole('button', { name: /excel/i })
    expect(xlsxButton).not.toBeDisabled()

    // Click the button — this triggers buildExportUrl
    fireEvent.click(xlsxButton)

    expect(buildExportUrl).toHaveBeenCalledWith('xlsx', filters)
  })

  // ---------------------------------------------------------------------------
  // Task 9.4 — dated filename in download attribute (spec requirement)
  // Fallback rule (mirrors backend):
  //   both dates present  → ventas-<desde_date>-<hasta_date>.<fmt>
  //   both dates absent   → ventas.<fmt>
  //   only desde present  → ventas-<desde_date>-all.<fmt>
  // ---------------------------------------------------------------------------

  it('sets a.download to dated filename when both dates are present', async () => {
    const { ReportesTable } = await import('./ReportesTable')
    const { fireEvent } = await import('@testing-library/react')
    const filters: ReportesFilters = {
      fecha_desde: '2026-06-01T00:00:00Z',
      fecha_hasta: '2026-06-22T23:59:59Z',
    }

    // Spy on document.createElement to capture the anchor element created by handleExport
    const createdAnchors: HTMLAnchorElement[] = []
    const origCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      const el = origCreate(tag)
      if (tag === 'a') createdAnchors.push(el as HTMLAnchorElement)
      return el
    })

    render(<ReportesTable rows={[mockRow]} filters={filters} />)

    const xlsxButton = screen.getByRole('button', { name: /excel/i })
    fireEvent.click(xlsxButton)

    expect(createdAnchors.length).toBeGreaterThan(0)
    const anchor = createdAnchors[createdAnchors.length - 1]
    expect(anchor.download).toBe('ventas-2026-06-01-2026-06-22.xlsx')

    vi.restoreAllMocks()
  })

  it('sets a.download to ventas.<fmt> when no dates are present (fallback)', async () => {
    const { ReportesTable } = await import('./ReportesTable')
    const { fireEvent } = await import('@testing-library/react')
    const filters: ReportesFilters = {}

    const createdAnchors: HTMLAnchorElement[] = []
    const origCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      const el = origCreate(tag)
      if (tag === 'a') createdAnchors.push(el as HTMLAnchorElement)
      return el
    })

    render(<ReportesTable rows={[mockRow]} filters={filters} />)

    const csvButton = screen.getByRole('button', { name: /csv/i })
    fireEvent.click(csvButton)

    expect(createdAnchors.length).toBeGreaterThan(0)
    const anchor = createdAnchors[createdAnchors.length - 1]
    expect(anchor.download).toBe('ventas.csv')

    vi.restoreAllMocks()
  })
})
