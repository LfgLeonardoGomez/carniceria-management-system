import axios from 'axios'
import type {
  Notificacion,
  NotificacionFilters,
  PaginatedNotificacionResponse,
} from '@/shared/types/notificacion'

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

export async function fetchNotificaciones(
  filters: NotificacionFilters = {},
): Promise<PaginatedNotificacionResponse> {
  const query = new URLSearchParams()
  if (filters.skip !== undefined) query.set('skip', String(filters.skip))
  if (filters.limit !== undefined) query.set('limit', String(filters.limit))
  if (filters.leida !== undefined) query.set('leida', String(filters.leida))

  const response = await api.get<PaginatedNotificacionResponse>(
    `/notificacion?${query.toString()}`,
  )
  return response.data
}

export async function marcarLeida(id: string): Promise<void> {
  await api.patch(`/notificacion/${id}/leida`)
}

export async function fetchNotificacionesNoLeidas(
  limit = 50,
): Promise<Notificacion[]> {
  const response = await fetchNotificaciones({ leida: false, limit })
  return response.items
}
