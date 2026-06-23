/**
 * TypeScript types for the cuentas-corrientes feature (C-14).
 *
 * Monetary values use `string` (Decimal-safe JSON from the backend).
 * No `any` — TypeScript strict mode enforced.
 */

// ---------------------------------------------------------------------------
// Movement
// ---------------------------------------------------------------------------

export interface MovimientoCC {
  id: string                      // UUID string
  tipo: 'deuda' | 'pago'
  importe: string                  // Decimal string, 2 d.p.
  saldo_resultante: string         // Decimal string, 2 d.p.
  venta_id: string | null          // UUID string or null
  fecha: string                    // ISO-8601 datetime string
}

// ---------------------------------------------------------------------------
// History / balance
// ---------------------------------------------------------------------------

export interface HistorialCCResponse {
  items: MovimientoCC[]
  total: number
  skip: number
  limit: number
  saldo_actual: string             // Decimal string, 2 d.p.
}

// ---------------------------------------------------------------------------
// Payment
// ---------------------------------------------------------------------------

export interface PagoCreate {
  importe: string                  // Decimal string, positive
}

export interface PagoResponse {
  movimiento: MovimientoCC
  saldo_actual: string             // Decimal string, 2 d.p.
}

// ---------------------------------------------------------------------------
// Export formats
// ---------------------------------------------------------------------------

export type ExportFormato = 'xlsx' | 'csv' | 'pdf'
