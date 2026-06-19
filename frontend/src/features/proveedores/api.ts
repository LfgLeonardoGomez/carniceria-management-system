import axios from 'axios'
import type {
  Proveedor,
  ProveedorCreate,
  ProveedorUpdate,
  PaginatedProveedorResponse,
  ProveedorHistorialResponse,
} from '@/shared/types/proveedor'

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

export async function fetchProveedores(params: {
  nombre?: string
  skip?: number
  limit?: number
  incluir_inactivos?: boolean
} = {}): Promise<PaginatedProveedorResponse> {
  const query = new URLSearchParams()
  if (params.nombre) query.set('nombre', params.nombre)
  if (params.skip !== undefined) query.set('skip', String(params.skip))
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.incluir_inactivos !== undefined) query.set('incluir_inactivos', String(params.incluir_inactivos))

  const response = await api.get<PaginatedProveedorResponse>(`/proveedores?${query.toString()}`)
  return response.data
}

export async function fetchProveedor(id: string): Promise<Proveedor> {
  const response = await api.get<Proveedor>(`/proveedores/${id}`)
  return response.data
}

export async function createProveedor(dto: ProveedorCreate): Promise<Proveedor> {
  const response = await api.post<Proveedor>('/proveedores', dto)
  return response.data
}

export async function updateProveedor(id: string, dto: ProveedorUpdate): Promise<Proveedor> {
  const response = await api.put<Proveedor>(`/proveedores/${id}`, dto)
  return response.data
}

export async function deleteProveedor(id: string): Promise<void> {
  await api.delete(`/proveedores/${id}`)
}

export async function fetchProveedorHistorial(
  id: string,
  params: { skip?: number; limit?: number } = {},
): Promise<ProveedorHistorialResponse> {
  const query = new URLSearchParams()
  if (params.skip !== undefined) query.set('skip', String(params.skip))
  if (params.limit !== undefined) query.set('limit', String(params.limit))

  const response = await api.get<ProveedorHistorialResponse>(`/proveedores/${id}/historial?${query.toString()}`)
  return response.data
}
