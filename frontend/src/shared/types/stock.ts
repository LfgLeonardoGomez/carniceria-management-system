export interface MovimientoStock {
  id: string
  empresa_id: string
  producto_id: string
  tipo: 'entrada_compra' | 'entrada_desposte' | 'salida_venta' | 'ajuste'
  cantidad_kilos: string
  stock_resultante: string
  referencia_id: string | null
  referencia_tipo: string | null
  motivo: string | null
  operador_id: string | null
  fecha: string
  created_at: string
}

export interface StockItem {
  producto_id: string
  nombre: string
  plu: string
  stock_actual: string
  stock_minimo: string | null
  estado: 'ok' | 'alerta' | 'critico'
}

export interface AlertaStockItem {
  producto_id: string
  nombre: string
  plu: string
  stock_actual: string
  stock_minimo: string
  estado: 'alerta' | 'critico'
}

export interface AjusteStockPayload {
  producto_id: string
  cantidad_kilos: string
  motivo: string
}

export interface PaginatedStockResponse {
  items: StockItem[]
  total: number
  skip: number
  limit: number
}

export interface PaginatedKardexResponse {
  items: MovimientoStock[]
  total: number
  skip: number
  limit: number
}
