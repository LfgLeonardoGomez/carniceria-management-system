import { describe, it, expect } from 'vitest'
import { parseSystelCode, SystelParseError } from './systelParser'

describe('parseSystelCode', () => {
  it('debería parsear código válido con peso entero (2000270048052)', () => {
    const result = parseSystelCode('2000270048052')
    expect(result).toEqual({ plu: '00027', pesoKg: 4.805 })
  })

  it('debería parsear código válido con peso pequeño (2000270001005)', () => {
    const result = parseSystelCode('2000270001005')
    expect(result).toEqual({ plu: '00027', pesoKg: 0.1 })
  })

  it('debería parsear código válido con peso máximo (2999999999995)', () => {
    const result = parseSystelCode('2999999999995')
    expect(result).toEqual({ plu: '99999', pesoKg: 999.999 })
  })

  it('debería retornar error para longitud inválida (12 dígitos)', () => {
    const result = parseSystelCode('200027004805')
    expect(result).toBeInstanceOf(SystelParseError)
    expect((result as SystelParseError).message).toMatch(/longitud/i)
  })

  it('debería retornar error para longitud inválida (14 dígitos)', () => {
    const result = parseSystelCode('20002700480520')
    expect(result).toBeInstanceOf(SystelParseError)
    expect((result as SystelParseError).message).toMatch(/longitud/i)
  })

  it('debería retornar error para caracteres no numéricos', () => {
    const result = parseSystelCode('20002700480A2')
    expect(result).toBeInstanceOf(SystelParseError)
    expect((result as SystelParseError).message).toMatch(/numérico/i)
  })

  it('debería retornar error para string vacío', () => {
    const result = parseSystelCode('')
    expect(result).toBeInstanceOf(SystelParseError)
    expect((result as SystelParseError).message).toMatch(/longitud/i)
  })

  it('debería retornar error para null/undefined', () => {
    // @ts-expect-error testing invalid input
    const resultNull = parseSystelCode(null)
    expect(resultNull).toBeInstanceOf(SystelParseError)

    // @ts-expect-error testing invalid input
    const resultUndefined = parseSystelCode(undefined)
    expect(resultUndefined).toBeInstanceOf(SystelParseError)
  })

  it('debería retornar error para prefijo distinto a 2', () => {
    const result = parseSystelCode('1000270048052')
    expect(result).toBeInstanceOf(SystelParseError)
    expect((result as SystelParseError).message).toMatch(/prefijo/i)
  })
})
