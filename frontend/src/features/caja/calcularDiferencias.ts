/**
 * Esperado-vs-real cash difference math for the caja close screen.
 *
 * Money is handled as decimal strings and computed in integer cents to avoid
 * floating-point error (project rule: never use float for money).
 */

export interface MontosPorMedio {
  efectivo: string
  transferencias: string
  tarjetas: string
}

export interface DiferenciasCaja {
  diferenciaEfectivo: string
  diferenciaTransferencias: string
  diferenciaTarjetas: string
  diferenciaTotal: string
  tieneDiferencia: boolean
}

/** Parse a decimal string into integer cents. Empty/invalid -> 0. */
function toCents(value: string): number {
  if (!value || value.trim() === '') return 0
  const normalized = value.replace(',', '.')
  const num = Number(normalized)
  if (Number.isNaN(num)) return 0
  return Math.round(num * 100)
}

/** Format integer cents back into a fixed-2 decimal string. */
function fromCents(cents: number): string {
  const sign = cents < 0 ? '-' : ''
  const abs = Math.abs(cents)
  const entero = Math.floor(abs / 100)
  const resto = abs % 100
  return `${sign}${entero}.${String(resto).padStart(2, '0')}`
}

export function calcularDiferencias(
  esperado: MontosPorMedio,
  real: MontosPorMedio,
): DiferenciasCaja {
  const difEfectivo = toCents(real.efectivo) - toCents(esperado.efectivo)
  const difTransferencias = toCents(real.transferencias) - toCents(esperado.transferencias)
  const difTarjetas = toCents(real.tarjetas) - toCents(esperado.tarjetas)
  const difTotal = difEfectivo + difTransferencias + difTarjetas

  return {
    diferenciaEfectivo: fromCents(difEfectivo),
    diferenciaTransferencias: fromCents(difTransferencias),
    diferenciaTarjetas: fromCents(difTarjetas),
    diferenciaTotal: fromCents(difTotal),
    tieneDiferencia: difTotal !== 0,
  }
}
