import { describe, expect, it } from 'vitest'
import type { FeatureRow, Kline } from '../../app/types/api'
import {
  featureToHistogram,
  featureToLine,
  klinesToCandles,
  klinesToVolume,
  lastValue,
  latestOpenTime,
  toUtcSeconds,
  valueAt,
  warmupInfo,
} from '../../app/utils/chart-mapping'

function kline(openTime: string, open: number, close: number): Kline {
  return { symbol: 'BTCUSDT', open_time: openTime, open, high: Math.max(open, close) + 1, low: Math.min(open, close) - 1, close, volume: 10 }
}

function feature(ts: string, sma20: number | null, macdHist: number | null = null): FeatureRow {
  return { symbol: 'BTCUSDT', timestamp: ts, sma_20: sma20, macd_histogram: macdHist }
}

// API devolve newest-first
const KLINES: Kline[] = [
  kline('2026-08-19T02:00:00Z', 100, 90),
  kline('2026-08-19T01:00:00Z', 95, 100),
  kline('2026-08-19T00:00:00Z', 90, 95),
]

describe('toUtcSeconds', () => {
  it('converts ISO to seconds (not ms)', () => {
    expect(toUtcSeconds('2026-08-19T00:00:00Z')).toBe(1787097600)
  })
})

describe('klinesToCandles', () => {
  it('reverses newest-first into ascending unique times', () => {
    const candles = klinesToCandles(KLINES)
    expect(candles.map(c => c.time)).toEqual([1787097600, 1787101200, 1787104800])
    expect(candles[0]).toMatchObject({ open: 90, close: 95 })
  })
  it('dedupes overlapping windows', () => {
    const dup = [...KLINES, kline('2026-08-19T01:00:00Z', 1, 2)]
    expect(klinesToCandles(dup)).toHaveLength(3)
  })
})

describe('klinesToVolume', () => {
  it('colors by candle direction', () => {
    const vol = klinesToVolume(KLINES, { up: 'U', down: 'D' })
    expect(vol.map(v => v.color)).toEqual(['U', 'U', 'D'])
  })
})

describe('featureToLine', () => {
  it('turns null (warm-up) into whitespace points, never zero', () => {
    const rows = [feature('2026-08-19T01:00:00Z', 101), feature('2026-08-19T00:00:00Z', null)]
    const line = featureToLine(rows, 'sma_20')
    expect(line).toEqual([{ time: 1787097600 }, { time: 1787101200, value: 101 }])
    expect('value' in line[0]!).toBe(false)
  })
})

describe('featureToHistogram', () => {
  it('colors positive/negative around zero', () => {
    const rows = [feature('2026-08-19T01:00:00Z', null, -2), feature('2026-08-19T00:00:00Z', null, 3), feature('2026-08-18T23:00:00Z', null, null)]
    const hist = featureToHistogram(rows, 'macd_histogram', { positive: 'P', negative: 'N' })
    expect(hist).toEqual([
      { time: 1787094000 },
      { time: 1787097600, value: 3, color: 'P' },
      { time: 1787101200, value: -2, color: 'N' },
    ])
  })
})

describe('warmupInfo', () => {
  it('reports first timestamp with a value', () => {
    const rows = [feature('2026-08-19T02:00:00Z', 3), feature('2026-08-19T01:00:00Z', 2), feature('2026-08-19T00:00:00Z', null)]
    expect(warmupInfo(rows, 'sma_20', 20)).toEqual({ firstValueAt: '2026-08-19T01:00:00Z', missing: null, hasAnyValue: true })
  })
  it('reports how many candles are missing when no value exists yet', () => {
    const rows = [feature('2026-08-19T01:00:00Z', null), feature('2026-08-19T00:00:00Z', null)]
    expect(warmupInfo(rows, 'sma_20', 200)).toEqual({ firstValueAt: null, missing: 198, hasAnyValue: false })
  })
})

describe('lastValue / valueAt / latestOpenTime', () => {
  const rows = [feature('2026-08-19T02:00:00Z', null), feature('2026-08-19T01:00:00Z', 7), feature('2026-08-19T00:00:00Z', 5)]
  it('lastValue skips trailing nulls', () => {
    expect(lastValue(rows, 'sma_20')).toBe(7)
  })
  it('valueAt matches by time', () => {
    expect(valueAt(rows, 'sma_20', toUtcSeconds('2026-08-19T00:00:00Z'))).toBe(5)
    expect(valueAt(rows, 'sma_20', toUtcSeconds('2026-08-19T02:00:00Z'))).toBeNull()
    expect(valueAt(rows, 'sma_20', toUtcSeconds('2020-01-01T00:00:00Z'))).toBeNull()
  })
  it('latestOpenTime picks the newest candle', () => {
    expect(latestOpenTime(KLINES)).toBe('2026-08-19T02:00:00Z')
    expect(latestOpenTime([])).toBeNull()
  })
})
