export interface Cliente {
  id: string
  empresa_id: string
  nombre: string
  apellido: string | null
  razon_social: string | null
  cuit: string | null
  telefono: string | null
  email: string | null
  direccion: string | null
  tipo_cliente: string
  limite_cuenta_corriente: string
  saldo_actual: string
  activo: boolean
  created_at: string
  updated_at: string
}

export interface ClienteCreate {
  nombre: string
  apellido?: string | null
  razon_social?: string | null
  cuit?: string | null
  telefono?: string | null
  email?: string | null
  direccion?: string | null
  tipo_cliente?: string
  limite_cuenta_corriente?: string
}

export interface ClienteUpdate {
  nombre?: string
  apellido?: string | null
  razon_social?: string | null
  cuit?: string | null
  telefono?: string | null
  email?: string | null
  direccion?: string | null
  tipo_cliente?: string
  limite_cuenta_corriente?: string
}

export interface VentaResumen {
  id: string
  fecha: string
  total: string
  estado: string
}

export interface PaginatedClienteResponse {
  items: Cliente[]
  total: number
  skip: number
  limit: number
}

export interface ClienteHistorialResponse {
  items: VentaResumen[]
  total: number
  skip: number
  limit: number
}
