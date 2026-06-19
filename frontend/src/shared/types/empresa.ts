export interface DatosFiscales {
  condicion_iva?: string
  inicio_actividades?: string
  punto_venta?: number
}

export interface ConfiguracionGeneral {
  timezone: string
  moneda: string
  idioma: string
}

export interface ParametrosOperativos {
  alerta_stock_minimo_umbral: string
  alerta_gasto_elevado_umbral: string
  alerta_deuda_vencida_dias: number
}

export interface EmpresaPublic {
  id: string
  nombre_comercial: string
  razon_social?: string
  cuit?: string
  domicilio?: string
  telefono?: string
  email?: string
  logo_url?: string
  datos_fiscales?: DatosFiscales
  configuracion_general?: ConfiguracionGeneral
  parametros_operativos?: ParametrosOperativos
  activa: boolean
  created_at: string
  updated_at: string
}

export interface EmpresaUpdate {
  nombre_comercial?: string
  razon_social?: string
  cuit?: string
  domicilio?: string
  telefono?: string
  email?: string
  datos_fiscales?: DatosFiscales
  configuracion_general?: ConfiguracionGeneral
  parametros_operativos?: ParametrosOperativos
}
