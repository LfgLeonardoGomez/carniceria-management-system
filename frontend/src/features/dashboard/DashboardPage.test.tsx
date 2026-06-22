import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardPage } from './DashboardPage'
import * as api from './api'
import type {
  GraficosResponse,
  IndicadoresResponse,
  RankingsResponse,
} from '@/shared/types/dashboard'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock('./api')

const mockIndicadores: IndicadoresResponse = {
  ventas_dia: '1500.00',
  ventas_mes: '45000.00',
  kilos_vendidos: '250.500',
  clientes_atendidos: 32,
  stock_critico: 3,
  gastos_mes: '8000.00',
  ganancia_bruta: '12000.00',
  ganancia_neta: '4000.00',
  ganancia_disponible: true,
}

const mockRankings: RankingsResponse = {
  productos_mas_vendidos: [
    { producto_id: 'p1', nombre: 'Asado', kilos: '85.500' },
    { producto_id: 'p2', nombre: 'Vacío', kilos: '62.000' },
  ],
}

const mockGraficos: GraficosResponse = {
  ventas_diarias: [{ fecha: '2024-06-20', total: '1500.00' }],
  ventas_mensuales: [{ periodo: '2024-06', total: '45000.00' }],
  distribucion_medio_pago: [
    { medio_pago: 'efectivo', total: '30000.00' },
    { medio_pago: 'tarjeta', total: '15000.00' },
  ],
  evolucion_ganancias: [{ periodo: '2024-06', ganancia_bruta: '12000.00' }],
  ganancia_disponible: true,
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

// ---------------------------------------------------------------------------
// Task 6.1 — Render with data
// ---------------------------------------------------------------------------
describe('DashboardPage — rendering with data', () => {
  beforeEach(() => {
    vi.mocked(api.fetchIndicadores).mockResolvedValue(mockIndicadores)
    vi.mocked(api.fetchRankings).mockResolvedValue(mockRankings)
    vi.mocked(api.fetchGraficos).mockResolvedValue(mockGraficos)
  })

  it('renders the page heading', async () => {
    renderDashboard()
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
  })

  it('shows ventas_dia KPI card', async () => {
    renderDashboard()
    await waitFor(() => {
      // Use testid for specificity
      expect(screen.getByTestId('kpi-ventas-dia')).toBeInTheDocument()
      expect(screen.getByTestId('kpi-ventas-dia').textContent).toMatch(/1[.,]500/)
    })
  })

  it('shows clientes_atendidos KPI card', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('32')).toBeInTheDocument()
    })
  })

  it('shows stock_critico KPI card', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  it('renders the rankings table with producto names', async () => {
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('Asado')).toBeInTheDocument()
      expect(screen.getByText('Vacío')).toBeInTheDocument()
    })
  })
})

// ---------------------------------------------------------------------------
// Task 6.2 — Hide ganancia cards when ganancia_disponible: false
// ---------------------------------------------------------------------------
describe('DashboardPage — ganancia gating', () => {
  it('hides ganancia cards when ganancia_disponible is false', async () => {
    const noSnapshotIndicadores: IndicadoresResponse = {
      ...mockIndicadores,
      ganancia_bruta: null,
      ganancia_neta: null,
      ganancia_disponible: false,
    }
    vi.mocked(api.fetchIndicadores).mockResolvedValue(noSnapshotIndicadores)
    vi.mocked(api.fetchRankings).mockResolvedValue(mockRankings)
    vi.mocked(api.fetchGraficos).mockResolvedValue({ ...mockGraficos, ganancia_disponible: false })

    renderDashboard()
    await waitFor(() => {
      // Ganancia bruta and neta cards must NOT appear
      expect(screen.queryByTestId('kpi-ganancia-bruta')).not.toBeInTheDocument()
      expect(screen.queryByTestId('kpi-ganancia-neta')).not.toBeInTheDocument()
    })
  })

  it('shows ganancia cards when ganancia_disponible is true', async () => {
    vi.mocked(api.fetchIndicadores).mockResolvedValue(mockIndicadores)
    vi.mocked(api.fetchRankings).mockResolvedValue(mockRankings)
    vi.mocked(api.fetchGraficos).mockResolvedValue(mockGraficos)

    renderDashboard()
    await waitFor(() => {
      expect(screen.getByTestId('kpi-ganancia-bruta')).toBeInTheDocument()
    })
  })
})

// ---------------------------------------------------------------------------
// Task 6.3 — Empty states
// ---------------------------------------------------------------------------
describe('DashboardPage — empty states', () => {
  it('shows empty rankings message when no products sold', async () => {
    vi.mocked(api.fetchIndicadores).mockResolvedValue({
      ...mockIndicadores,
      ventas_dia: '0.00',
      ventas_mes: '0.00',
    })
    vi.mocked(api.fetchRankings).mockResolvedValue({ productos_mas_vendidos: [] })
    vi.mocked(api.fetchGraficos).mockResolvedValue({
      ...mockGraficos,
      ventas_diarias: [],
      distribucion_medio_pago: [],
    })

    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText(/sin ventas/i)).toBeInTheDocument()
    })
  })
})
