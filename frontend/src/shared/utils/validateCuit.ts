export function validateCuit(cuit: string): boolean {
  if (!/^\d{11}$/.test(cuit)) return false

  const base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
  const digits = cuit.split('').map(Number)
  const checksum = base.reduce((sum, b, i) => sum + b * digits[i], 0)
  const remainder = checksum % 11
  let verifier = 11 - remainder

  if (verifier === 11) verifier = 0
  else if (verifier === 10) {
    const tipo = parseInt(cuit.slice(0, 2), 10)
    if ([20, 23, 24, 27].includes(tipo)) verifier = 9
    else if ([30, 33, 34].includes(tipo)) verifier = 4
    else return false
  }

  return verifier === digits[10]
}
