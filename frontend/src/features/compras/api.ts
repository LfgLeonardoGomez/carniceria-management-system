import axios from 'axios'
import type {
  Compra,
  CompraCreate,
  CompraUpdate,
  PaginatedCompraResponse,
  CompraFilters,
} from '@/shared/types/compra'

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

export async function fetchCompras(
  filters: CompraFilters = {},
): Promise<PaginatedCompraResponse> {
  const query = new URLSearchParams()
  if (filters.proveedor_id) query.set('proveedor_id', filters.proveedor_id)
  if (filters.fecha_desde) query.set('fecha_desde', filters.fecha_desde)
  if (filters.fecha_hasta) query.set('fecha_hasta', filters.fecha_hasta)
  if (filters.skip !== undefined) query.set('skip', String(filters.skip))
  if (filters.limit !== undefined) query.set('limit', String(filters.limit))
  if (filters.incluir_anuladas) query.set('incluir_anuladas', 'true')

  const response = await api.get<PaginatedCompraResponse>(`/compra?${query.toString()}`)
  return response.data
}

export async function fetchCompra(id: string): Promise<Compra> {
  const response = await api.get<Compra>(`/compra/${id}`)
  return response.data
}

export async function createCompra(dto: CompraCreate): Promise<Compra> {
  const response = await api.post<Compra>('/compra', dto)
  return response.data
}

export async function updateCompra(id: string, dto: CompraUpdate): Promise<Compra> {
  const response = await api.put<Compra>(`/compra/${id}`, dto)
  return response.data
}

export async function deleteCompra(id: string): Promise<void> {
  await api.delete(`/compra/${id}`)
}
