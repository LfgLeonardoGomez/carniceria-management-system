export interface CorteDesposte {
  id: string
  tipo_corte: TipoCorte
  kilos_obtenidos: string
  porcentaje_rendimiento: string
  costo_asignado: string
  costo_final_por_kilo: string
  producto_id: string | null
  producto?: {
    id: string
    nombre: string
    plu: string
  }
  created_at: string
  updated_at: string
}

export type TipoCorte =
  | 'asado'
  | 'vacio'
  | 'nalga'
  | 'cuadril'
  | 'peceto'
  | 'bola_de_lomo'
  | 'lomo'
  | 'matambre'
  | 'costilla'
  | 'osobuco'
  | 'molida'
  | 'otros'

export const TIPOS_CORTE: TipoCorte[] = [
  'asado',
  'vacio',
  'nalga',
  'cuadril',
  'peceto',
  'bola_de_lomo',
  'lomo',
  'matambre',
  'costilla',
  'osobuco',
  'molida',
  'otros',
]

export interface MovimientoStockCompacto {
  id: string
  tipo: string
  cantidad_kilos: string
  stock_resultante: string
  producto_id: string
  fecha: string
}

export interface Desposte {
  id: string
  empresa_id: string
  compra_id: string
  compra?: {
    id: string
    fecha: string
    peso_total: string
    costo_total: string
    proveedor?: {
      id: string
      nombre: string
    }
  }
  fecha: string
  operador_id: string
  operador?: {
    id: string
    nombre: string | null
    apellido: string | null
  }
  estado: 'en_proceso' | 'finalizado'
  rendimiento_total: string
  merma: string
  cortes: CorteDesposte[]
  movimientos_stock: MovimientoStockCompacto[]
  created_at: string
  updated_at: string
}

export interface DesposteCreate {
  compra_id: string
  fecha: string
  operador_id: string
}

export interface CorteDesposteCreate {
  tipo_corte: TipoCorte
  kilos_obtenidos: string
  producto_id?: string | null
}

export interface DesposteFilters {
  fecha?: string
  estado?: string
  skip?: number
  limit?: number
}

export interface PaginatedDesposteResponse {
  items: Desposte[]
  total: number
  skip: number
  limit: number
}
