import axios from 'axios'
import type {
  UsuarioCreate,
  UsuarioUpdate,
  UsuarioPublic,
  UsuarioListResponse,
  PerfilPublic,
  PerfilUpdate,
  ContrasenaTemporalResponse,
  CambioContrasenaPayload,
} from '@/shared/types/usuario'

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

function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d: unknown) => String(d)).join(', ')
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Error inesperado'
}

export async function listarUsuarios(
  skip: number,
  limit: number,
  activo?: boolean | null,
): Promise<UsuarioListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
  if (activo !== null && activo !== undefined) {
    params.append('activo', String(activo))
  }
  const response = await api.get<UsuarioListResponse>(`/usuarios?${params.toString()}`)
  return response.data
}

export async function crearUsuario(dto: UsuarioCreate): Promise<ContrasenaTemporalResponse> {
  const response = await api.post<ContrasenaTemporalResponse>('/usuarios', dto)
  return response.data
}

export async function actualizarUsuario(id: string, dto: UsuarioUpdate): Promise<UsuarioPublic> {
  const response = await api.put<UsuarioPublic>(`/usuarios/${id}`, dto)
  return response.data
}

export async function desactivarUsuario(id: string): Promise<UsuarioPublic> {
  const response = await api.patch<UsuarioPublic>(`/usuarios/${id}/desactivar`)
  return response.data
}

export async function reactivarUsuario(id: string): Promise<UsuarioPublic> {
  const response = await api.patch<UsuarioPublic>(`/usuarios/${id}/reactivar`)
  return response.data
}

export async function obtenerPerfil(): Promise<PerfilPublic> {
  const response = await api.get<PerfilPublic>('/usuarios/me')
  return response.data
}

export async function actualizarPerfil(dto: PerfilUpdate): Promise<PerfilPublic> {
  const response = await api.put<PerfilPublic>('/usuarios/me', dto)
  return response.data
}

export async function cambiarContrasena(dto: CambioContrasenaPayload): Promise<void> {
  await api.patch('/usuarios/me/contrasena', dto)
}

export { extractErrorMessage }
export type {
  UsuarioCreate,
  UsuarioUpdate,
  UsuarioPublic,
  UsuarioListResponse,
  PerfilPublic,
  PerfilUpdate,
  ContrasenaTemporalResponse,
  CambioContrasenaPayload,
}
