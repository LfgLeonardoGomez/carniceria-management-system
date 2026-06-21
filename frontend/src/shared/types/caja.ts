export interface Caja {
  id: string
  empresa_id: string
  estado: 'abierta' | 'cerrada'
  monto_inicial: string
  monto_final: string | null
  fecha_apertura: string
  fecha_cierre: string | null
  usuario_apertura_id: string | null
  usuario_cierre_id: string | null
}

export interface EsperadoCaja {
  efectivo: string
  transferencias: string
  tarjetas: string
}

export interface CajaActualResponse {
  caja: Caja
  esperado: EsperadoCaja
}

export interface AperturaCajaRequest {
  efectivo_inicial: string
}

export type TipoMovimientoManual = 'retiro' | 'ingreso_manual'

export interface MovimientoCajaRequest {
  tipo: TipoMovimientoManual
  importe: string
  descripcion?: string | null
}

export interface MovimientoCajaRead {
  id: string
  caja_id: string
  tipo: string
  medio: string | null
  importe: string
  descripcion: string | null
  fecha: string
}

export interface CierreCajaRequest {
  efectivo_real: string
  transferencias_real: string
  tarjetas_real: string
}

export interface DiferenciasCajaServer {
  diferencia_efectivo: string
  diferencia_transferencias: string
  diferencia_tarjetas: string
  diferencia_total: string
  tiene_diferencia: boolean
  diferencia_significativa: boolean
}

export interface CierreCajaResponse {
  caja: Caja
  esperado: EsperadoCaja
  reales: EsperadoCaja
  diferencias: DiferenciasCajaServer
}
