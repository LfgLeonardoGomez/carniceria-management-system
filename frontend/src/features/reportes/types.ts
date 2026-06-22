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

// ---------------------------------------------------------------------------
// C-18 — Financial report types
// NOTE: APPEND-ONLY. Do not edit C-17 types above.
// ---------------------------------------------------------------------------

/**
 * Valid temporal groupings for the financial report.
 * Invalid values are rejected by the API with HTTP 422.
 */
export type GroupBy = 'dia' | 'semana' | 'mes' | 'anio'

/**
 * One period bucket in the financial report.
 *
 * ventas and gastos are always present (string Decimal).
 * costos, utilidad_bruta, utilidad_neta are null when any sale in the bucket
 * lacks a cost snapshot (pre-snapshot historical sale). NULL is NEVER zero —
 * render as "no disponible", not "0.00".
 */
export interface FinancieroPeriodoRow {
  periodo: string               // e.g. "2026-06", "2026-W26", "2026"
  ventas: string                // Decimal string, always present
  gastos: string                // Decimal string, always present
  costos: string | null         // null = cost snapshot missing for this bucket
  utilidad_bruta: string | null
  utilidad_neta: string | null
}

export interface ReporteFinancieroResponse {
  group_by: GroupBy
  rows: FinancieroPeriodoRow[]
}

export interface ReporteFinancieroFilters {
  group_by: GroupBy
  fecha_desde?: string   // ISO-8601 datetime string or undefined
  fecha_hasta?: string
}
