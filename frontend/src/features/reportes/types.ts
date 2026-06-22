/**
 * TypeScript types for the reportes feature (C-17).
 *
 * Monetary values use `string` (Decimal-safe JSON representation from the backend).
 * No `any` — TypeScript strict mode enforced.
 */

export interface VentaReporteRow {
  venta_id: string
  fecha: string          // ISO-8601 datetime string
  cliente_nombre: string
  productos: string      // comma-separated product names
  total_kilos: string    // Decimal string, 3 d.p.
  subtotal: string       // Decimal string, 2 d.p.
  total: string          // Decimal string, 2 d.p.
  medios_pago: string    // comma-separated payment methods
  ganancia_estimada: string | null  // null = pre-snapshot historical row
}

export interface ReportesFilters {
  fecha_desde?: string   // ISO-8601 datetime string or undefined
  fecha_hasta?: string   // ISO-8601 datetime string or undefined
  cliente_id?: string    // UUID string or undefined
}

export type ExportFormato = 'xlsx' | 'csv' | 'pdf'

export interface ReporteVentasResponse {
  rows: VentaReporteRow[]
  total: number
  skip: number
  limit: number
}
