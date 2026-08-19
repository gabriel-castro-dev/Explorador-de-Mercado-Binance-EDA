import { describe, expect, it } from 'vitest'
import {
  arrowOf,
  formatAgo,
  formatCompact,
  formatNumber,
  formatPercent,
  formatPrice,
  formatUtc,
  formatUtcShort,
  hoursSince,
  priceDecimals,
  toneOf,
} from '../../app/utils/format'

describe('formatUtc', () => {
  it('renders day, month (pt-BR) and HH:MM in UTC', () => {
    expect(formatUtc('2026-08-19T00:00:00Z')).toBe('19 ago 00:00 UTC')
    expect(formatUtcShort('2026-08-18T14:00:00+00:00')).toBe('18 ago 14:00')
  })
  it('omits time / adds year on demand', () => {
    expect(formatUtcShort('2026-01-05T10:30:00Z', { withTime: false, withYear: true })).toBe('5 jan 2026')
  })
  it('returns em dash for invalid dates', () => {
    expect(formatUtc('not-a-date')).toBe('—')
  })
})

describe('formatAgo / hoursSince', () => {
  const now = new Date('2026-08-19T06:00:00Z')
  it('minutes, hours, days', () => {
    expect(formatAgo('2026-08-19T05:48:00Z', now)).toBe('há 12 min')
    expect(formatAgo('2026-08-19T00:00:00Z', now)).toBe('há 6 h')
    expect(formatAgo('2026-08-17T23:00:00Z', now)).toBe('há 31 h')
    expect(formatAgo('2026-08-16T00:00:00Z', now)).toBe('há 3 d')
    expect(formatAgo('2026-08-19T05:59:40Z', now)).toBe('agora')
  })
  it('hoursSince is fractional and never negative-surprising', () => {
    expect(hoursSince('2026-08-19T00:00:00Z', now)).toBeCloseTo(6)
    expect(hoursSince('garbage', now)).toBe(Number.POSITIVE_INFINITY)
  })
})

describe('numbers pt-BR', () => {
  it('groups thousands with dot and decimals with comma', () => {
    expect(formatNumber(113512.3, 1)).toBe('113.512,3')
    expect(formatNumber(1284.5, 1)).toBe('1.284,5')
    expect(formatNumber(-26.9, 1)).toBe('−26,9')
    expect(formatNumber(2048.9, 1, { sign: true })).toBe('+2.048,9')
  })
  it('price decimals follow magnitude', () => {
    expect(priceDecimals(113512)).toBe(1)
    expect(priceDecimals(186.4)).toBe(2)
    expect(priceDecimals(3.012)).toBe(3)
    expect(priceDecimals(0.231)).toBe(4)
    expect(priceDecimals(0.00001234)).toBe(8)
    expect(formatPrice(0.231)).toBe('0,2310')
    expect(formatPrice(null)).toBe('—')
  })
  it('percent with explicit sign and space before %', () => {
    expect(formatPercent(1.84)).toBe('+1,84 %')
    expect(formatPercent(-0.62)).toBe('−0,62 %')
    expect(formatPercent(0)).toBe('+0,00 %')
    expect(formatPercent(undefined)).toBe('—')
  })
  it('compact volumes', () => {
    expect(formatCompact(4.33e9)).toBe('4,33 bi')
    expect(formatCompact(896e6)).toBe('896,00 mi')
    expect(formatCompact(38412)).toBe('38.412')
    expect(formatCompact(51.2)).toBe('51,2')
  })
})

describe('tone / arrow', () => {
  it('never uses em dash for zero change', () => {
    expect(toneOf(0)).toBe('flat')
    expect(arrowOf(0)).toBe('')
    expect(arrowOf(2)).toBe('▲')
    expect(arrowOf(-2)).toBe('▼')
    expect(toneOf(null)).toBeNull()
  })
})
