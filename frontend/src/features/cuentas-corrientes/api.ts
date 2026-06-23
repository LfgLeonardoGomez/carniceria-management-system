/**
 * API client for the cuentas-corrientes feature (C-14).
 *
 * Base URL: VITE_API_URL (default: http://localhost:8000)
 * Auth: Bearer token from localStorage — same pattern as rentabilidad/api.ts.
 * No `any` — TypeScript strict mode enforced.
 */
import axios from 'axios'
import type {
  ExportFormato,
  HistorialCCResponse,
  PagoCreate,
  PagoResponse,
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
 * Fetch movement history + balance for a customer.
 * GET /cuentas-corrientes/{cliente_id}
 */
export async function fetchHistorialCC(
  clienteId: string,
  skip = 0,
  limit = 50,
): Promise<HistorialCCResponse> {
  const response = await api.get<HistorialCCResponse>(
    `/cuentas-corrientes/${clienteId}`,
    { params: { skip, limit } },
  )
  return response.data
}

/**
 * Register a payment for a customer.
 * POST /cuentas-corrientes/{cliente_id}/pagos
 */
export async function registrarPago(
  clienteId: string,
  data: PagoCreate,
): Promise<PagoResponse> {
  const response = await api.post<PagoResponse>(
    `/cuentas-corrientes/${clienteId}/pagos`,
    data,
  )
  return response.data
}

/**
 * Download the account statement.
 * GET /cuentas-corrientes/{cliente_id}/estado-cuenta
 *
 * Returns a Blob so the caller can trigger a browser download.
 */
export async function descargarEstadoCuenta(
  clienteId: string,
  formato: ExportFormato = 'pdf',
): Promise<Blob> {
  const response = await api.get(
    `/cuentas-corrientes/${clienteId}/estado-cuenta`,
    {
      params: { formato },
      responseType: 'blob',
    },
  )
  return response.data as Blob
}
