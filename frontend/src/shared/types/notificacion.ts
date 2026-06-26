/** Tipos compartidos del módulo Notificaciones. */

export type TipoNotificacion =
  | 'stock_bajo'
  | 'stock_critico'
  | 'deuda_vencida'
  | 'gasto_elevado'
  | 'diferencia_caja'

export const TIPOS_NOTIFICACION: TipoNotificacion[] = [
  'stock_bajo',
  'stock_critico',
  'deuda_vencida',
  'gasto_elevado',
  'diferencia_caja',
]

export const TIPOS_NOTIFICACION_LABELS: Record<TipoNotificacion, string> = {
  stock_bajo: 'Stock bajo',
  stock_critico: 'Stock crítico',
  deuda_vencida: 'Deuda vencida',
  gasto_elevado: 'Gasto elevado',
  diferencia_caja: 'Diferencia de caja',
}

export interface Notificacion {
  id: string
  empresa_id: string
  tipo: TipoNotificacion
  mensaje: string
  leida: boolean
  fecha_lectura: string | null
  entidad_tipo: string
  entidad_id: string
  created_at: string
}

export interface PaginatedNotificacionResponse {
  items: Notificacion[]
  total: number
  skip: number
  limit: number
}

export interface NotificacionFilters {
  skip?: number
  limit?: number
  leida?: boolean
}
