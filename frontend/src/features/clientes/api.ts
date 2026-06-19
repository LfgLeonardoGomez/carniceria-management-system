import axios from 'axios'
import type {
  Cliente,
  ClienteCreate,
  ClienteUpdate,
  PaginatedClienteResponse,
  ClienteHistorialResponse,
} from '@/shared/types/cliente'

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

export async function fetchClientes(params: {
  search?: string
  tipo_cliente?: string
  skip?: number
  limit?: number
  activo?: boolean
} = {}): Promise<PaginatedClienteResponse> {
  const query = new URLSearchParams()
  if (params.search) query.set('q', params.search)
  if (params.tipo_cliente) query.set('tipo_cliente', params.tipo_cliente)
  if (params.skip !== undefined) query.set('skip', String(params.skip))
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.activo !== undefined) query.set('activo', String(params.activo))

  const response = await api.get<PaginatedClienteResponse>(`/cliente?${query.toString()}`)
  return response.data
}

export async function fetchCliente(id: string): Promise<Cliente> {
  const response = await api.get<Cliente>(`/cliente/${id}`)
  return response.data
}

export async function createCliente(dto: ClienteCreate): Promise<Cliente> {
  const response = await api.post<Cliente>('/cliente', dto)
  return response.data
}

export async function updateCliente(id: string, dto: ClienteUpdate): Promise<Cliente> {
  const response = await api.put<Cliente>(`/cliente/${id}`, dto)
  return response.data
}

export async function deleteCliente(id: string): Promise<Cliente> {
  const response = await api.delete<Cliente>(`/cliente/${id}`)
  return response.data
}

export async function fetchClienteHistorial(
  id: string,
  params: { skip?: number; limit?: number } = {},
): Promise<ClienteHistorialResponse> {
  const query = new URLSearchParams()
  if (params.skip !== undefined) query.set('skip', String(params.skip))
  if (params.limit !== undefined) query.set('limit', String(params.limit))

  const response = await api.get<ClienteHistorialResponse>(`/cliente/${id}/historial?${query.toString()}`)
  return response.data
}
