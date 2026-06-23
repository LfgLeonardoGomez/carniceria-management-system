/**
 * TypeScript types for the rentabilidad feature (C-19).
 *
 * Monetary values use `string` (Decimal-safe JSON representation from the
 * backend — the API serialises Python Decimal as strings, never floats).
 * No `any` — TypeScript strict mode enforced.
 *
 * NULL margin means cost data is unavailable. NULL is NEVER zero — render as
 * "no disponible" or a distinct visual indicator, not "0.00".
 */

// ---------------------------------------------------------------------------
// Request filters
// ---------------------------------------------------------------------------

/**
 * Ordering direction for GET /rentabilidad/productos.
 * "mayor" → highest margin first (default).
 * "menor" → lowest margin first (least profitable).
 */
export type OrdenRentabilidad = 'mayor' | 'menor'

export interface RentabilidadProductosFilters {
  fecha_desde?: string          // ISO-8601 datetime string or undefined
  fecha_hasta?: string          // ISO-8601 datetime string or undefined
  orden?: OrdenRentabilidad     // default: "mayor"
  top?: number                  // positive integer or undefined (no limit)
}

export interface RentabilidadCortesFilters {
  fecha_desde?: string          // ISO-8601 datetime string or undefined
  fecha_hasta?: string          // ISO-8601 datetime string or undefined
}

// ---------------------------------------------------------------------------
// Response shapes — mirror backend schemas exactly
// ---------------------------------------------------------------------------

/**
 * One row in the product profitability ranking.
 *
 * ganancia and margen_porcentaje are null when any sale line for this product
 * is missing a cost snapshot. NULL is not zero.
 * Products with null margin are always ordered last, regardless of `orden`.
 */
export interface ProductoRentabilidadRow {
  producto_id: string           // UUID string
  nombre: string
  ventas: string                // Decimal string, 2 d.p. — always present
  ganancia: string | null       // null = cost snapshot unavailable
  margen_porcentaje: string | null  // null = cost snapshot unavailable
}

export interface RentabilidadProductosResponse {
  rows: ProductoRentabilidadRow[]
}

/**
 * One row in the cut margin view.
 *
 * precio_venta_promedio, margen_por_kilo, and margen_porcentaje are null when
 * the linked product has no sales in the requested date range.
 * costo_por_kilo is always present (sourced from CorteDesposte).
 * Cuts with producto_id = NULL are excluded by the backend — never appear here.
 */
export interface CorteRentabilidadRow {
  tipo_corte: string
  producto_id: string           // UUID string (never null — excluded at backend)
  nombre_producto: string
  costo_por_kilo: string        // Decimal string, 2 d.p. — always present
  precio_venta_promedio: string | null  // null = no sales in range
  margen_por_kilo: string | null
  margen_porcentaje: string | null
}

export interface RentabilidadCortesResponse {
  rows: CorteRentabilidadRow[]
}
