import { describe, expect, it } from 'vitest'
import type { Ticker24h } from '../../app/types/api'
import { filterTickers, latestSnapshotAt, sortTickers, spreadPercent, tickerHasData, trackedSymbols } from '../../app/utils/tickers'

function t(symbol: string, quote: number | null, pct: number | null = 0, openTime = '2026-08-19T14:00:00Z'): Ticker24h {
  return { symbol, open_time: openTime, close_time: openTime, quote_volume: quote, price_change_percent: pct, last_price: quote === null ? null : 1 }
}

const ROWS = [t('ETHUSDT', 2.65e9, -0.62), t('PEPEUSDT', null, null), t('BTCUSDT', 4.33e9, 1.84), t('SOLUSDT', 1.81e9, 3.11)]

describe('sortTickers', () => {
  it('sorts desc by default with nulls last', () => {
    expect(sortTickers(ROWS, 'quote_volume').map(r => r.symbol)).toEqual(['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'PEPEUSDT'])
  })
  it('asc keeps nulls last too', () => {
    expect(sortTickers(ROWS, 'price_change_percent', 'asc').map(r => r.symbol)).toEqual(['ETHUSDT', 'BTCUSDT', 'SOLUSDT', 'PEPEUSDT'])
  })
  it('sorts strings (symbol) alphabetically', () => {
    expect(sortTickers(ROWS, 'symbol', 'asc').map(r => r.symbol)).toEqual(['BTCUSDT', 'ETHUSDT', 'PEPEUSDT', 'SOLUSDT'])
  })
  it('does not mutate input', () => {
    const copy = [...ROWS]
    sortTickers(ROWS, 'quote_volume')
    expect(ROWS).toEqual(copy)
  })
})

describe('filterTickers', () => {
  const names = (s: string) => (s === 'BTCUSDT' ? 'Bitcoin / Tether' : undefined)
  it('matches by symbol or name, case-insensitive', () => {
    expect(filterTickers(ROWS, 'bitc', names).map(r => r.symbol)).toEqual(['BTCUSDT'])
    expect(filterTickers(ROWS, 'sol', names).map(r => r.symbol)).toEqual(['SOLUSDT'])
    expect(filterTickers(ROWS, '  ', names)).toHaveLength(4)
  })
})

describe('latestSnapshotAt / spreadPercent / tickerHasData', () => {
  it('picks the newest close_time', () => {
    const rows = [t('A', 1, 0, '2026-08-19T13:00:00Z'), t('B', 1, 0, '2026-08-19T14:00:00Z')]
    expect(latestSnapshotAt(rows)).toBe('2026-08-19T14:00:00Z')
    expect(latestSnapshotAt([])).toBeNull()
  })
  it('spread in percent of bid', () => {
    expect(spreadPercent({ bid_price: 100, ask_price: 100.5 })).toBeCloseTo(0.5)
    expect(spreadPercent({ bid_price: null, ask_price: 1 })).toBeNull()
  })
  it('tickerHasData is false when every key field is null', () => {
    expect(tickerHasData(t('X', null, null))).toBe(false)
    expect(tickerHasData(t('Y', 1))).toBe(true)
  })
})

describe('trackedSymbols', () => {
  it('mantém só os símbolos com candles, na ordem recebida', () => {
    const rows = [
      { symbol: 'BTCUSDT', tracked: true },
      { symbol: 'CTSIUSDT', tracked: false },
      { symbol: 'ETHUSDT', tracked: true },
    ]
    expect(trackedSymbols(rows).map(s => s.symbol)).toEqual(['BTCUSDT', 'ETHUSDT'])
  })

  it('lista vazia sem rastreados', () => {
    expect(trackedSymbols([{ symbol: 'CTSIUSDT', tracked: false }])).toEqual([])
  })
})
