import axios from 'axios'
import type {
  Desposte,
  DesposteCreate,
  CorteDesposteCreate,
  PaginatedDesposteResponse,
  DesposteFilters,
} from '@/shared/types/desposte'

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

export async function fetchDespostes(
  filters: DesposteFilters = {},
): Promise<PaginatedDesposteResponse> {
  const query = new URLSearchParams()
  if (filters.fecha) query.set('fecha', filters.fecha)
  if (filters.estado) query.set('estado', filters.estado)
  if (filters.skip !== undefined) query.set('skip', String(filters.skip))
  if (filters.limit !== undefined) query.set('limit', String(filters.limit))

  const response = await api.get<PaginatedDesposteResponse>(`/desposte?${query.toString()}`)
  return response.data
}

export async function fetchDesposte(id: string): Promise<Desposte> {
  const response = await api.get<Desposte>(`/desposte/${id}`)
  return response.data
}

export async function createDesposte(dto: DesposteCreate): Promise<Desposte> {
  const response = await api.post<Desposte>('/desposte', dto)
  return response.data
}

export async function addCorte(
  desposteId: string,
  dto: CorteDesposteCreate,
): Promise<Desposte> {
  const response = await api.post<Desposte>(`/desposte/${desposteId}/cortes`, dto)
  return response.data
}

export async function finalizarDesposte(id: string): Promise<Desposte> {
  const response = await api.post<Desposte>(`/desposte/${id}/finalizar`)
  return response.data
}
