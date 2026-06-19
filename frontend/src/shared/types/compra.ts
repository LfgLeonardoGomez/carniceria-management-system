export interface Compra {
  id: string
  empresa_id: string
  proveedor_id: string
  proveedor?: {
    id: string
    nombre: string
  }
  fecha: string
  cantidad_medias_reses: number
  peso_total: string
  costo_total: string
  costo_por_kilo: string
  costo_promedio_historico: string
  observaciones: string | null
  estado: string
  created_at: string
  updated_at: string
}

export interface CompraCreate {
  fecha: string
  proveedor_id: string
  cantidad_medias_reses: number
  peso_total: string
  costo_total: string
  observaciones?: string | null
}

export interface CompraUpdate {
  fecha?: string
  cantidad_medias_reses?: number
  peso_total?: string
  costo_total?: string
  observaciones?: string | null
}

export interface CompraFilters {
  proveedor_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  skip?: number
  limit?: number
  incluir_anuladas?: boolean
}

export interface PaginatedCompraResponse {
  items: Compra[]
  total: number
  skip: number
  limit: number
  costo_promedio_historico?: string | null
}
