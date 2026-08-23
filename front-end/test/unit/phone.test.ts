import { describe, expect, it } from 'vitest'
import { formatBrPhoneDisplay, maskBrPhoneInput, parsePhoneInput } from '../../app/utils/phone'

describe('parsePhoneInput', () => {
  it('celular BR com 11 dígitos → +55', () => {
    expect(parsePhoneInput('(11) 98123-4567')).toBe('+5511981234567')
    expect(parsePhoneInput('11981234567')).toBe('+5511981234567')
  })

  it('fixo BR com 10 dígitos → +55', () => {
    expect(parsePhoneInput('(31) 3123-4567')).toBe('+553131234567')
  })

  it('já em E.164 passa direto (com limpeza de separadores)', () => {
    expect(parsePhoneInput('+5511981234567')).toBe('+5511981234567')
    expect(parsePhoneInput('+55 (11) 98123-4567')).toBe('+5511981234567')
    expect(parsePhoneInput('+14155552671')).toBe('+14155552671')
  })

  it('55 + número completo sem "+" é aceito como BR', () => {
    expect(parsePhoneInput('5511981234567')).toBe('+5511981234567')
  })

  it('inválidos → null', () => {
    expect(parsePhoneInput('')).toBeNull()
    expect(parsePhoneInput('123')).toBeNull()
    expect(parsePhoneInput('+011981234567')).toBeNull() // E.164 não começa com 0
    expect(parsePhoneInput('981234567')).toBeNull() // sem DDD
  })
})

describe('formatBrPhoneDisplay', () => {
  it('E.164 BR → máscara local', () => {
    expect(formatBrPhoneDisplay('+5511981234567')).toBe('(11) 98123-4567')
    expect(formatBrPhoneDisplay('+553131234567')).toBe('(31) 3123-4567')
  })

  it('outros países ficam como estão; vazio → vazio', () => {
    expect(formatBrPhoneDisplay('+14155552671')).toBe('+14155552671')
    expect(formatBrPhoneDisplay(null)).toBe('')
  })
})

describe('maskBrPhoneInput', () => {
  it('mascara progressivamente a digitação', () => {
    expect(maskBrPhoneInput('1')).toBe('(1')
    expect(maskBrPhoneInput('119812')).toBe('(11) 9812')
    expect(maskBrPhoneInput('11981234567')).toBe('(11) 98123-4567')
  })

  it('entrada internacional não é mascarada', () => {
    expect(maskBrPhoneInput('+5511981234567')).toBe('+5511981234567')
  })

  it('trunca além de 11 dígitos', () => {
    expect(maskBrPhoneInput('119812345678999')).toBe('(11) 98123-4567')
  })
})
