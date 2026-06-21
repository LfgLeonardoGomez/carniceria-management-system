export type CategoriaGasto =
  | 'alquiler'
  | 'empleados'
  | 'luz'
  | 'agua'
  | 'gas'
  | 'internet'
  | 'combustible'
  | 'impuestos'
  | 'mantenimiento'
  | 'insumos'
  | 'otros'

export const CATEGORIAS_GASTO: CategoriaGasto[] = [
  'alquiler',
  'empleados',
  'luz',
  'agua',
  'gas',
  'internet',
  'combustible',
  'impuestos',
  'mantenimiento',
  'insumos',
  'otros',
]

export const CATEGORIAS_GASTO_LABELS: Record<CategoriaGasto, string> = {
  alquiler: 'Alquiler',
  empleados: 'Empleados',
  luz: 'Luz',
  agua: 'Agua',
  gas: 'Gas',
  internet: 'Internet',
  combustible: 'Combustible',
  impuestos: 'Impuestos',
  mantenimiento: 'Mantenimiento',
  insumos: 'Insumos',
  otros: 'Otros',
}

export type MedioPagoGasto = 'efectivo' | 'transferencia' | 'debito' | 'credito' | 'cheque'

export const MEDIOS_PAGO_GASTO: MedioPagoGasto[] = [
  'efectivo',
  'transferencia',
  'debito',
  'credito',
  'cheque',
]

export const MEDIOS_PAGO_GASTO_LABELS: Record<MedioPagoGasto, string> = {
  efectivo: 'Efectivo',
  transferencia: 'Transferencia',
  debito: 'Débito',
  credito: 'Crédito',
  cheque: 'Cheque',
}

export interface Gasto {
  id: string
  empresa_id: string
  fecha: string
  categoria: CategoriaGasto
  descripcion: string | null
  importe: string
  medio_pago: MedioPagoGasto
  created_at: string
  updated_at: string
}

export interface GastoCreate {
  fecha: string
  categoria: CategoriaGasto
  descripcion?: string | null
  importe: string
  medio_pago: MedioPagoGasto
}

export interface GastoUpdate {
  fecha?: string
  categoria?: CategoriaGasto
  descripcion?: string | null
  importe?: string
  medio_pago?: MedioPagoGasto
}

export interface GastoListResponse {
  items: Gasto[]
  total: number
  skip: number
  limit: number
}

export interface GastoFilters {
  categoria?: CategoriaGasto
  fecha_desde?: string
  fecha_hasta?: string
  skip?: number
  limit?: number
}
