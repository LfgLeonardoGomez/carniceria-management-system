import { describe, it, expect } from 'vitest'
import { calcularDiferencias } from '@/features/caja/calcularDiferencias'

describe('calcularDiferencias', () => {
  it('returns zero differences when real matches esperado', () => {
    const result = calcularDiferencias(
      { efectivo: '140.00', transferencias: '50.00', tarjetas: '200.00' },
      { efectivo: '140.00', transferencias: '50.00', tarjetas: '200.00' },
    )
    expect(result.diferenciaEfectivo).toBe('0.00')
    expect(result.diferenciaTotal).toBe('0.00')
    expect(result.tieneDiferencia).toBe(false)
  })

  it('computes a faltante (negative) when real is less than esperado', () => {
    const result = calcularDiferencias(
      { efectivo: '140.00', transferencias: '0.00', tarjetas: '0.00' },
      { efectivo: '130.00', transferencias: '0.00', tarjetas: '0.00' },
    )
    expect(result.diferenciaEfectivo).toBe('-10.00')
    expect(result.diferenciaTotal).toBe('-10.00')
    expect(result.tieneDiferencia).toBe(true)
  })

  it('sums differences across all media for the total', () => {
    const result = calcularDiferencias(
      { efectivo: '100.00', transferencias: '50.00', tarjetas: '30.00' },
      { efectivo: '105.00', transferencias: '52.00', tarjetas: '30.00' },
    )
    expect(result.diferenciaEfectivo).toBe('5.00')
    expect(result.diferenciaTransferencias).toBe('2.00')
    expect(result.diferenciaTarjetas).toBe('0.00')
    expect(result.diferenciaTotal).toBe('7.00')
    expect(result.tieneDiferencia).toBe(true)
  })

  it('treats empty real inputs as zero', () => {
    const result = calcularDiferencias(
      { efectivo: '100.00', transferencias: '0.00', tarjetas: '0.00' },
      { efectivo: '', transferencias: '', tarjetas: '' },
    )
    expect(result.diferenciaEfectivo).toBe('-100.00')
    expect(result.diferenciaTotal).toBe('-100.00')
  })
})
