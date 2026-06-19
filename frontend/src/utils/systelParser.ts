/**
 * Error de parseo de código SYSTEL.
 */
export class SystelParseError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'SystelParseError'
  }
}

/**
 * Resultado exitoso del parseo de un código SYSTEL.
 */
export interface SystelParseResult {
  /** PLU del producto (5 dígitos, zero-padded). */
  plu: string
  /** Peso en kilogramos con 3 decimales de precisión. */
  pesoKg: number
}

/**
 * Parsea un código de barras SYSTEL de 13 dígitos.
 *
 * Formato:
 * - Posición 1: prefijo "2" (producto pesado)
 * - Posiciones 2-6: PLU (5 dígitos, zero-padded)
 * - Posiciones 7-12: peso en gramos con 2 decimales implícitos
 * - Posición 13: checksum (validación opcional para v1.0)
 *
 * @param code - String de 13 dígitos numéricos
 * @returns {SystelParseResult} objeto con plu y pesoKg
 * @returns {SystelParseError} error descriptivo si el código es inválido
 *
 * @example
 * parseSystelCode('2000270048052')
 * // => { plu: '00027', pesoKg: 4.805 }
 */
export function parseSystelCode(code: string): SystelParseResult | SystelParseError {
  if (typeof code !== 'string') {
    return new SystelParseError('El código debe ser un string')
  }

  if (code.length !== 13) {
    return new SystelParseError(`Longitud inválida: esperado 13 dígitos, recibido ${code.length}`)
  }

  if (!/^\d{13}$/.test(code)) {
    return new SystelParseError('Formato numérico inválido: solo se permiten dígitos 0-9')
  }

  if (code[0] !== '2') {
    return new SystelParseError(`Prefijo de producto pesado inválido: esperado "2", recibido "${code[0]}"`)
  }

  const plu = code.slice(1, 6)
  const pesoGramosStr = code.slice(6, 12)
  const pesoGramos = parseInt(pesoGramosStr, 10)
  const pesoKg = pesoGramos / 1000

  return { plu, pesoKg }
}
