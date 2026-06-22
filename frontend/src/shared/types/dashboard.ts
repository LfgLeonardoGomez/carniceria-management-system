export interface ProductoRankingItem {
  producto_id: string
  nombre: string
  kilos: string
}

export interface IndicadoresResponse {
  ventas_dia: string
  ventas_mes: string
  kilos_vendidos: string
  clientes_atendidos: number
  stock_critico: number
  gastos_mes: string
  ganancia_bruta: string | null
  ganancia_neta: string | null
  ganancia_disponible: boolean
}

export interface RankingsResponse {
  productos_mas_vendidos: ProductoRankingItem[]
}

export interface VentaDiariaItem {
  fecha: string
  total: string
}

export interface VentaMensualItem {
  periodo: string
  total: string
}

export interface MedioPagoItem {
  medio_pago: string
  total: string
}

export interface EvolucionGananciaItem {
  periodo: string
  ganancia_bruta: string | null
}

export interface GraficosResponse {
  ventas_diarias: VentaDiariaItem[]
  ventas_mensuales: VentaMensualItem[]
  distribucion_medio_pago: MedioPagoItem[]
  evolucion_ganancias: EvolucionGananciaItem[]
  ganancia_disponible: boolean
}
