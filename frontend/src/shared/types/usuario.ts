export interface UsuarioPublic {
  id: string
  nombre?: string
  apellido?: string
  email: string
  rol?: string
  activo: boolean
  empresa_id?: string
  ultimo_acceso?: string
  created_at: string
  updated_at: string
}

export interface UsuarioListResponse {
  items: UsuarioPublic[]
  total: number
  skip: number
  limit: number
}

export interface UsuarioCreate {
  nombre: string
  apellido: string
  email: string
  rol_id: string
}

export interface UsuarioUpdate {
  nombre?: string
  apellido?: string
  email?: string
  rol_id?: string
}

export interface PerfilPublic {
  id: string
  nombre?: string
  apellido?: string
  email: string
  rol?: string
  empresa?: string
  ultimo_acceso?: string
}

export interface PerfilUpdate {
  nombre?: string
  apellido?: string
  email?: string
}

export interface ContrasenaTemporalResponse {
  usuario: UsuarioPublic
  contrasena_temporal: string
}

export interface CambioContrasenaPayload {
  contrasena_actual: string
  contrasena_nueva: string
}

export const ROLES = [
  { id: '9d1f08ec-a0a9-5fbc-aaa6-a63ec0cbb704', nombre: 'Administrador' },
  { id: '96ccee1d-f141-5267-b275-9ddc692187e6', nombre: 'Encargado' },
  { id: 'f5241add-fdb4-57c9-a51b-4f2974b2bb52', nombre: 'Cajero' },
  { id: 'c81449ff-4e4a-585a-8768-f5040b95b68d', nombre: 'Vendedor' },
] as const
