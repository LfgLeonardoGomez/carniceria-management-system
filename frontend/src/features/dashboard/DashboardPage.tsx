import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type {
  GraficosResponse,
  IndicadoresResponse,
  RankingsResponse,
} from '@/shared/types/dashboard'
import { fetchGraficos, fetchIndicadores, fetchRankings } from './api'
import { useAuthStore } from '@/store/authStore'

const REPORTES_ROLES = ['admin', 'administrador', 'encargado']

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------
interface KpiCardProps {
  label: string
  value: string | number
  'data-testid'?: string
}

function KpiCard({ label, value, 'data-testid': testId }: KpiCardProps) {
  return (
    <div className="kpi-card" data-testid={testId}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Format helpers (no external Decimal lib needed for display)
// ---------------------------------------------------------------------------
function formatMoney(value: string): string {
  // Display with locale formatting (2 decimals)
  const num = parseFloat(value)
  return num.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatKilos(value: string): string {
  const num = parseFloat(value)
  return num.toLocaleString('es-AR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

// ---------------------------------------------------------------------------
// Rankings Table
// ---------------------------------------------------------------------------
interface RankingsTableProps {
  rankings: RankingsResponse | null
  loading: boolean
}

function RankingsTable({ rankings, loading }: RankingsTableProps) {
  if (loading) return <p>Cargando ranking...</p>
  if (!rankings || rankings.productos_mas_vendidos.length === 0) {
    return <p className="empty-state">Sin ventas registradas este mes</p>
  }
  return (
    <table className="rankings-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Producto</th>
          <th>Kilos vendidos</th>
        </tr>
      </thead>
      <tbody>
        {rankings.productos_mas_vendidos.map((item, idx) => (
          <tr key={item.producto_id}>
            <td>{idx + 1}</td>
            <td>{item.nombre}</td>
            <td>{formatKilos(item.kilos)} kg</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// ---------------------------------------------------------------------------
// Medio de Pago Distribution
// ---------------------------------------------------------------------------
interface MedioDistribucionProps {
  graficos: GraficosResponse | null
}

function MedioDistribucion({ graficos }: MedioDistribucionProps) {
  if (!graficos || graficos.distribucion_medio_pago.length === 0) {
    return <p className="empty-state">Sin datos de distribución este mes</p>
  }
  return (
    <ul className="medio-pago-list">
      {graficos.distribucion_medio_pago.map((item) => (
        <li key={item.medio_pago}>
          <span className="medio-nombre">{item.medio_pago}</span>
          <span className="medio-total">$ {formatMoney(item.total)}</span>
        </li>
      ))}
    </ul>
  )
}

// ---------------------------------------------------------------------------
// Daily Sales list (simple — no charting lib required)
// ---------------------------------------------------------------------------
interface DailySalesProps {
  graficos: GraficosResponse | null
}

function DailySalesList({ graficos }: DailySalesProps) {
  if (!graficos || graficos.ventas_diarias.length === 0) {
    return <p className="empty-state">Sin ventas en los últimos 7 días</p>
  }
  return (
    <ul className="ventas-diarias-list">
      {graficos.ventas_diarias.map((item) => (
        <li key={item.fecha}>
          <span>{item.fecha}</span>
          <span>$ {formatMoney(item.total)}</span>
        </li>
      ))}
    </ul>
  )
}

// ---------------------------------------------------------------------------
// DashboardPage
// ---------------------------------------------------------------------------
export function DashboardPage() {
  const { user } = useAuthStore()
  const [indicadores, setIndicadores] = useState<IndicadoresResponse | null>(null)
  const [rankings, setRankings] = useState<RankingsResponse | null>(null)
  const [graficos, setGraficos] = useState<GraficosResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [ind, rnk, graf] = await Promise.all([
          fetchIndicadores(),
          fetchRankings(),
          fetchGraficos(),
        ])
        if (!cancelled) {
          setIndicadores(ind)
          setRankings(rnk)
          setGraficos(graf)
        }
      } catch (err) {
        if (!cancelled) {
          setError('No se pudo cargar el dashboard. Intentá de nuevo.')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [])

  return (
    <div className="dashboard-page">
      <nav className="dashboard-nav">
        <span>Dashboard</span>
        {user && REPORTES_ROLES.includes(user.rol) && (
          <Link to="/reportes" className="nav-link-reportes">
            Reportes
          </Link>
        )}
      </nav>
      <h1>Dashboard</h1>

      {error && <div className="error-banner">{error}</div>}

      {/* KPI Cards */}
      <section className="kpi-grid" aria-label="Indicadores del negocio">
        {loading ? (
          <p>Cargando indicadores...</p>
        ) : indicadores ? (
          <>
            <KpiCard
              label="Ventas hoy"
              value={`$ ${formatMoney(indicadores.ventas_dia)}`}
              data-testid="kpi-ventas-dia"
            />
            <KpiCard
              label="Ventas del mes"
              value={`$ ${formatMoney(indicadores.ventas_mes)}`}
              data-testid="kpi-ventas-mes"
            />
            <KpiCard
              label="Kilos vendidos (mes)"
              value={`${formatKilos(indicadores.kilos_vendidos)} kg`}
              data-testid="kpi-kilos"
            />
            <KpiCard
              label="Clientes atendidos hoy"
              value={indicadores.clientes_atendidos}
              data-testid="kpi-clientes"
            />
            <KpiCard
              label="Stock crítico"
              value={indicadores.stock_critico}
              data-testid="kpi-stock-critico"
            />
            <KpiCard
              label="Gastos del mes"
              value={`$ ${formatMoney(indicadores.gastos_mes)}`}
              data-testid="kpi-gastos"
            />

            {/* Financial KPIs — shown only when ganancia_disponible */}
            {indicadores.ganancia_disponible && indicadores.ganancia_bruta !== null && (
              <KpiCard
                label="Ganancia bruta (mes)"
                value={`$ ${formatMoney(indicadores.ganancia_bruta)}`}
                data-testid="kpi-ganancia-bruta"
              />
            )}
            {indicadores.ganancia_disponible && indicadores.ganancia_neta !== null && (
              <KpiCard
                label="Ganancia neta (mes)"
                value={`$ ${formatMoney(indicadores.ganancia_neta)}`}
                data-testid="kpi-ganancia-neta"
              />
            )}
          </>
        ) : null}
      </section>

      {/* Ventas diarias (últimos 7 días) */}
      <section className="section-ventas-diarias">
        <h2>Ventas últimos 7 días</h2>
        <DailySalesList graficos={graficos} />
      </section>

      {/* Distribución medio de pago */}
      <section className="section-medio-pago">
        <h2>Distribución por medio de pago</h2>
        <MedioDistribucion graficos={graficos} />
      </section>

      {/* Rankings */}
      <section className="section-rankings">
        <h2>Productos más vendidos (mes)</h2>
        <RankingsTable rankings={rankings} loading={loading} />
      </section>
    </div>
  )
}
