export interface Proveedor {
  id: string
  empresa_id: string
  nombre: string
  cuit: string | null
  telefono: string | null
  email: string | null
  direccion: string | null
  activo: boolean
  created_at: string
  updated_at: string
}

export interface ProveedorCreate {
  nombre: string
  cuit?: string | null
  telefono?: string | null
  email?: string | null
  direccion?: string | null
}

export interface ProveedorUpdate {
  nombre?: string
  cuit?: string | null
  telefono?: string | null
  email?: string | null
  direccion?: string | null
}

export interface ProveedorFilters {
  search?: string
  skip?: number
  limit?: number
  incluir_inactivos?: boolean
}

export interface PaginatedProveedorResponse {
  items: Proveedor[]
  total: number
  skip: number
  limit: number
}

export interface CompraResumen {
  id: string
  fecha: string
  cantidad_medias_reses: number
  peso_total: string
  costo_total: string
  costo_por_kilo: string
  observaciones: string | null
}

export interface ProveedorHistorialResponse {
  items: CompraResumen[]
  total: number
  skip: number
  limit: number
}
