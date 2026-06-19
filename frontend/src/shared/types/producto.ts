export interface CategoriaProducto {
  id: string
  empresa_id: string | null
  nombre: string
  created_at: string
  updated_at: string
}

export interface Producto {
  id: string
  empresa_id: string
  plu: string
  nombre: string
  categoria_id: string | null
  precio_publico: string
  precio_mayorista: string
  costo_por_kilo: string
  margen: string
  stock_actual: string
  stock_minimo: string | null
  activo: boolean
  created_at: string
  updated_at: string
}

export interface ProductoCreate {
  plu: string
  nombre: string
  categoria_id: string | null
  precio_publico: string
  precio_mayorista: string
  costo_por_kilo: string
  stock_actual: string
  stock_minimo?: string | null
}

export interface ProductoUpdate {
  plu?: string
  nombre?: string
  categoria_id?: string | null
  precio_publico?: string
  precio_mayorista?: string
  costo_por_kilo?: string
  stock_actual?: string
  stock_minimo?: string | null
}

export interface PaginatedProductoResponse {
  items: Producto[]
  total: number
  skip: number
  limit: number
}

export interface PaginatedCategoriaResponse {
  items: CategoriaProducto[]
  total: number
  skip: number
  limit: number
}

export interface ImportPreview {
  session_id: string
  total_filas: number
  filas_validas: ImportPreviewRow[]
  filas_invalidas: ImportPreviewRow[]
  validas_count: number
  invalidas_count: number
}

export interface ImportPreviewRow {
  row_num: number
  plu: string
  nombre: string
  categoria: string
  precio_publico: string
  precio_mayorista: string
  costo_por_kilo: string
  stock_actual: string
  stock_minimo: string | null
  errores?: string[]
}

export interface ImportConfirmResult {
  creados: number
  errores: number
  total_validas: number
  total_invalidas: number
}
