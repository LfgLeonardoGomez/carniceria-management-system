import axios from 'axios'
import type {
  Gasto,
  GastoCreate,
  GastoUpdate,
  GastoListResponse,
  GastoFilters,
} from '@/shared/types/gasto'

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

export async function fetchGastos(filters: GastoFilters = {}): Promise<GastoListResponse> {
  const query = new URLSearchParams()
  if (filters.categoria) query.set('categoria', filters.categoria)
  if (filters.fecha_desde) query.set('fecha_desde', filters.fecha_desde)
  if (filters.fecha_hasta) query.set('fecha_hasta', filters.fecha_hasta)
  if (filters.skip !== undefined) query.set('skip', String(filters.skip))
  if (filters.limit !== undefined) query.set('limit', String(filters.limit))

  const response = await api.get<GastoListResponse>(`/gasto?${query.toString()}`)
  return response.data
}

export async function fetchGasto(id: string): Promise<Gasto> {
  const response = await api.get<Gasto>(`/gasto/${id}`)
  return response.data
}

export async function createGasto(dto: GastoCreate): Promise<Gasto> {
  const response = await api.post<Gasto>('/gasto', dto)
  return response.data
}

export async function updateGasto(id: string, dto: GastoUpdate): Promise<Gasto> {
  const response = await api.put<Gasto>(`/gasto/${id}`, dto)
  return response.data
}

export async function deleteGasto(id: string): Promise<void> {
  await api.delete(`/gasto/${id}`)
}
