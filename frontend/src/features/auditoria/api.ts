import axios from 'axios'
import type {
  AuditoriaFilters,
  AuditoriaRegistro,
  PaginatedAuditoriaResponse,
} from '@/shared/types/auditoria'

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

export async function fetchAuditoria(
  filters: AuditoriaFilters = {},
): Promise<PaginatedAuditoriaResponse> {
  const query = new URLSearchParams()
  if (filters.skip !== undefined) query.set('skip', String(filters.skip))
  if (filters.limit !== undefined) query.set('limit', String(filters.limit))
  if (filters.usuario_id) query.set('usuario_id', filters.usuario_id)
  if (filters.fecha_desde) query.set('fecha_desde', filters.fecha_desde)
  if (filters.fecha_hasta) query.set('fecha_hasta', filters.fecha_hasta)
  if (filters.accion) query.set('accion', filters.accion)
  if (filters.entidad_tipo) query.set('entidad_tipo', filters.entidad_tipo)

  const response = await api.get<PaginatedAuditoriaResponse>(
    `/auditoria?${query.toString()}`,
  )
  return response.data
}

/** Descarga un blob client-side con la lista actual de registros. */
export function exportarCSV(registros: AuditoriaRegistro[]): Blob {
  const cabecera = [
    'id',
    'fecha',
    'hora',
    'usuario_id',
    'accion',
    'entidad_tipo',
    'entidad_id',
    'payload',
  ]
  const escape = (v: unknown): string => {
    if (v === null || v === undefined) return ''
    const s = typeof v === 'string' ? v : JSON.stringify(v)
    if (s.includes('"') || s.includes(',') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`
    }
    return s
  }
  const filas = registros.map((r) =>
    [
      r.id,
      r.fecha,
      r.hora,
      r.usuario_id ?? '',
      r.accion,
      r.entidad_tipo,
      r.entidad_id ?? '',
      r.payload ?? '',
    ]
      .map(escape)
      .join(','),
  )
  const csv = [cabecera.join(','), ...filas].join('\n')
  return new Blob([csv], { type: 'text/csv;charset=utf-8' })
}

export function exportarJSON(registros: AuditoriaRegistro[]): Blob {
  const json = JSON.stringify(registros, null, 2)
  return new Blob([json], { type: 'application/json;charset=utf-8' })
}
