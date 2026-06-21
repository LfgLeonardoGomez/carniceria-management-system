import axios from 'axios'
import type {
  Caja,
  CajaActualResponse,
  AperturaCajaRequest,
  MovimientoCajaRequest,
  MovimientoCajaRead,
  CierreCajaRequest,
  CierreCajaResponse,
} from '@/shared/types/caja'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function fetchCajaActual(): Promise<CajaActualResponse | null> {
  try {
    const response = await api.get<CajaActualResponse>('/caja/actual')
    return response.data
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) {
      return null
    }
    throw err
  }
}

export async function abrirCaja(dto: AperturaCajaRequest): Promise<Caja> {
  const response = await api.post<Caja>('/caja/apertura', dto)
  return response.data
}

export async function registrarMovimiento(
  dto: MovimientoCajaRequest,
): Promise<MovimientoCajaRead> {
  const response = await api.post<MovimientoCajaRead>('/caja/movimientos', dto)
  return response.data
}

export async function cerrarCaja(dto: CierreCajaRequest): Promise<CierreCajaResponse> {
  const response = await api.post<CierreCajaResponse>('/caja/cierre', dto)
  return response.data
}
