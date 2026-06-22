/**
 * API client for the reportes feature.
 *
 * Base URL: VITE_API_URL (default: http://localhost:8000)
 * Auth: Bearer token from localStorage, same pattern as dashboard/api.ts
 */
import axios from 'axios'
import type {
  ReportesFilters,
  ReporteVentasResponse,
  ReporteFinancieroFilters,
  ReporteFinancieroResponse,
} from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * Fetch the paginated sales report from the backend.
 * Maps ReportesFilters keys to query params (undefined values are omitted).
 */
export async function fetchReportesVentas(
  filters: ReportesFilters,
  skip = 0,
  limit = 50,
): Promise<ReporteVentasResponse> {
  const params: Record<string, string | number> = { skip, limit }
  if (filters.fecha_desde !== undefined) params.fecha_desde = filters.fecha_desde
  if (filters.fecha_hasta !== undefined) params.fecha_hasta = filters.fecha_hasta
  if (filters.cliente_id !== undefined) params.cliente_id = filters.cliente_id

  const response = await api.get<ReporteVentasResponse>('/reportes/ventas', { params })
  return response.data
}

/**
 * Build the export URL for the download link.
 * The browser handles the file download via an <a download> element.
 */
export function buildExportUrl(
  formato: 'xlsx' | 'csv' | 'pdf',
  filters: ReportesFilters,
): string {
  const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/reportes/ventas/exportar'
  const params = new URLSearchParams({ formato })
  if (filters.fecha_desde) params.set('fecha_desde', filters.fecha_desde)
  if (filters.fecha_hasta) params.set('fecha_hasta', filters.fecha_hasta)
  if (filters.cliente_id) params.set('cliente_id', filters.cliente_id)
  return `${base}?${params.toString()}`
}

// ---------------------------------------------------------------------------
// C-18 — Financial report API (APPEND-ONLY; do not edit C-17 functions above)
// ---------------------------------------------------------------------------

/**
 * Fetch the financial indicators report from GET /reportes/financieros.
 *
 * Returns per-period rows with ventas, costos, gastos, utilidad_bruta,
 * and utilidad_neta. Null indicators mean cost data is unavailable — never
 * treat null as zero on the frontend.
 */
export async function fetchReporteFinanciero(
  filters: ReporteFinancieroFilters,
): Promise<ReporteFinancieroResponse> {
  const params: Record<string, string> = { group_by: filters.group_by }
  if (filters.fecha_desde !== undefined) params.fecha_desde = filters.fecha_desde
  if (filters.fecha_hasta !== undefined) params.fecha_hasta = filters.fecha_hasta

  const response = await api.get<ReporteFinancieroResponse>('/reportes/financieros', { params })
  return response.data
}
