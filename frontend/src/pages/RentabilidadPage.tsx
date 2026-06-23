/**
 * RentabilidadPage — /rentabilidad route (Task 8.4 + 8.5).
 *
 * Three tabs:
 *   1. Más/Menos rentable (CA-1/CA-2) — useRentabilidadProductos
 *   2. Cortes desposte (CA-3)          — useRentabilidadCortes
 *   3. General (CA-4)                  — reuses useReporteFinanciero (C-18)
 *
 * Role guard: only administrador and encargado (reportes:read).
 * TypeScript strict: no `any`.
 */
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { RentabilidadFilters } from '@/features/rentabilidad/RentabilidadFilters'
import { RentabilidadProductosTable } from '@/features/rentabilidad/RentabilidadProductosTable'
import { RentabilidadCortesTable } from '@/features/rentabilidad/RentabilidadCortesTable'
import { useRentabilidadProductos, useRentabilidadCortes } from '@/features/rentabilidad/useRentabilidad'
import { useReporteFinanciero } from '@/features/reportes/useReporteFinanciero'
import { FinancieroTable } from '@/features/reportes/FinancieroTable'
import type { OrdenRentabilidad, RentabilidadProductosFilters, RentabilidadCortesFilters } from '@/features/rentabilidad/types'

type Tab = 'productos' | 'cortes' | 'general'

const ALLOWED_ROLES = ['admin', 'administrador', 'encargado']

export function RentabilidadPage(): JSX.Element {
  const { user } = useAuthStore()

  if (!user || !ALLOWED_ROLES.includes(user.rol)) {
    return (
      <div className="page-container" data-testid="rentabilidad-unauthorized">
        <p>No autorizado</p>
      </div>
    )
  }

  return <RentabilidadContent />
}

function RentabilidadContent(): JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('productos')
  const [fechaDesde, setFechaDesde] = useState<string | undefined>()
  const [fechaHasta, setFechaHasta] = useState<string | undefined>()
  const [orden, setOrden] = useState<OrdenRentabilidad>('mayor')
  const [top, setTop] = useState<number | undefined>()

  const productoFilters: RentabilidadProductosFilters = { fecha_desde: fechaDesde, fecha_hasta: fechaHasta, orden, top }
  const corteFilters: RentabilidadCortesFilters = { fecha_desde: fechaDesde, fecha_hasta: fechaHasta }

  const {
    rows: productosRows,
    isLoading: productosLoading,
    error: productosError,
  } = useRentabilidadProductos(productoFilters)

  const {
    rows: cortesRows,
    isLoading: cortesLoading,
    error: cortesError,
  } = useRentabilidadCortes(corteFilters)

  const {
    rows: financieroRows,
    isLoading: financieroLoading,
    error: financieroError,
  } = useReporteFinanciero({ group_by: 'mes', fecha_desde: fechaDesde, fecha_hasta: fechaHasta })

  return (
    <div className="page-container rentabilidad-page" data-testid="rentabilidad-page">
      <h1>Rentabilidad</h1>

      {/* Shared date-range filters */}
      <RentabilidadFilters
        fechaDesde={fechaDesde}
        fechaHasta={fechaHasta}
        onFechaDesdeChange={setFechaDesde}
        onFechaHastaChange={setFechaHasta}
      />

      {/* Tab navigation */}
      <nav data-testid="rentabilidad-tabs" style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button
          data-testid="tab-productos"
          aria-selected={activeTab === 'productos'}
          onClick={() => setActiveTab('productos')}
        >
          Por producto
        </button>
        <button
          data-testid="tab-cortes"
          aria-selected={activeTab === 'cortes'}
          onClick={() => setActiveTab('cortes')}
        >
          Por corte
        </button>
        <button
          data-testid="tab-general"
          aria-selected={activeTab === 'general'}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
      </nav>

      {/* Tab content */}
      {activeTab === 'productos' && (
        <section data-testid="tab-content-productos">
          {productosLoading && <p data-testid="rentabilidad-prod-loading">Cargando...</p>}
          {!productosLoading && productosError && (
            <p data-testid="rentabilidad-prod-error">Error al cargar datos.</p>
          )}
          {!productosLoading && !productosError && (
            <RentabilidadProductosTable
              rows={productosRows}
              orden={orden}
              onOrdenChange={setOrden}
              top={top}
              onTopChange={setTop}
            />
          )}
        </section>
      )}

      {activeTab === 'cortes' && (
        <section data-testid="tab-content-cortes">
          {cortesLoading && <p data-testid="rentabilidad-cortes-loading">Cargando...</p>}
          {!cortesLoading && cortesError && (
            <p data-testid="rentabilidad-cortes-error">Error al cargar datos.</p>
          )}
          {!cortesLoading && !cortesError && (
            <RentabilidadCortesTable rows={cortesRows} />
          )}
        </section>
      )}

      {activeTab === 'general' && (
        <section data-testid="tab-content-general">
          {financieroLoading && <p data-testid="rentabilidad-general-loading">Cargando...</p>}
          {!financieroLoading && financieroError && (
            <p data-testid="rentabilidad-general-error">Error al cargar datos.</p>
          )}
          {!financieroLoading && !financieroError && (
            <FinancieroTable rows={financieroRows} />
          )}
        </section>
      )}
    </div>
  )
}
