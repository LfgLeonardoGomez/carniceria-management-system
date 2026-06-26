/** Tipos compartidos del módulo Auditoría. */

export interface AuditoriaRegistro {
  id: string
  empresa_id: string
  usuario_id: string | null
  accion: string
  entidad_tipo: string
  entidad_id: string | null
  payload: Record<string, unknown> | null
  fecha: string
  hora: string
  created_at: string
}

export interface PaginatedAuditoriaResponse {
  items: AuditoriaRegistro[]
  total: number
  skip: number
  limit: number
}

export interface AuditoriaFilters {
  skip?: number
  limit?: number
  usuario_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  accion?: string
  entidad_tipo?: string
}
