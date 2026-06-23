/**
 * API client for the rentabilidad feature (C-19).
 *
 * Base URL: VITE_API_URL (default: http://localhost:8000)
 * Auth: Bearer token from localStorage, same pattern as reportes/api.ts.
 * No `any` — TypeScript strict mode enforced.
 */
import axios from 'axios'
import type {
  RentabilidadProductosFilters,
  RentabilidadCortesFilters,
  RentabilidadProductosResponse,
  RentabilidadCortesResponse,
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
 * Fetch the product profitability ranking from GET /rentabilidad/productos.
 *
 * Products with null margin (missing cost snapshot) are always ordered last
 * by the backend, regardless of the `orden` param. Render null as
 * "no disponible" — never treat null as zero.
 */
export async function fetchRentabilidadProductos(
  filters: RentabilidadProductosFilters,
): Promise<RentabilidadProductosResponse> {
  const params: Record<string, string | number> = {}
  if (filters.fecha_desde !== undefined) params.fecha_desde = filters.fecha_desde
  if (filters.fecha_hasta !== undefined) params.fecha_hasta = filters.fecha_hasta
  if (filters.orden !== undefined) params.orden = filters.orden
  if (filters.top !== undefined) params.top = filters.top

  const response = await api.get<RentabilidadProductosResponse>(
    '/rentabilidad/productos',
    { params },
  )
  return response.data
}

/**
 * Fetch the cut margin view from GET /rentabilidad/cortes.
 *
 * Rows with precio_venta_promedio = null have no sales in the range.
 * Cuts with producto_id = NULL are excluded by the backend — they never appear.
 */
export async function fetchRentabilidadCortes(
  filters: RentabilidadCortesFilters,
): Promise<RentabilidadCortesResponse> {
  const params: Record<string, string> = {}
  if (filters.fecha_desde !== undefined) params.fecha_desde = filters.fecha_desde
  if (filters.fecha_hasta !== undefined) params.fecha_hasta = filters.fecha_hasta

  const response = await api.get<RentabilidadCortesResponse>(
    '/rentabilidad/cortes',
    { params },
  )
  return response.data
}
