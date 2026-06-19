import { describe, it, expect } from 'vitest'
import { validateCuit } from '@/shared/utils/validateCuit'

describe('validateCuit', () => {
  it('validates a real empresa CUIT', () => {
    expect(validateCuit('30616874582')).toBe(true)
  })

  it('validates a persona fisica CUIT', () => {
    expect(validateCuit('20280206343')).toBe(true)
  })

  it('validates special case verifier 10 for persona', () => {
    expect(validateCuit('20000000019')).toBe(true)
  })

  it('validates special case verifier 10 for empresa', () => {
    expect(validateCuit('30000000044')).toBe(true)
  })

  it('rejects incorrect verifier', () => {
    expect(validateCuit('20280206345')).toBe(false)
  })

  it('rejects 10 digits', () => {
    expect(validateCuit('2028020634')).toBe(false)
  })

  it('rejects 12 digits', () => {
    expect(validateCuit('202802063434')).toBe(false)
  })

  it('rejects letters', () => {
    expect(validateCuit('20A28020634')).toBe(false)
  })

  it('rejects empty string', () => {
    expect(validateCuit('')).toBe(false)
  })
})
