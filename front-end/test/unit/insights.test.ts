import { describe, expect, it } from 'vitest'
import { splitReading, volatilityTop, volumeTop } from '../../app/utils/insights'
import type { FeatureRow, Kline, Ticker24h } from '../../app/types/api'

function feature(atr: number | null): FeatureRow {
  return { symbol: 'X', timestamp: '2026-08-22T00:00:00Z', atr_14: atr } as FeatureRow
}

function kline(openTime: string, quoteVolume: number | null): Kline {
  return {
    symbol: 'X',
    open_time: openTime,
    open: 1,
    high: 1,
    low: 1,
    close: 1,
    volume: 1,
    quote_asset_volume: quoteVolume,
  } as Kline
}

function ticker(symbol: string, quoteVolume: number | null): Ticker24h {
  return { symbol, open_time: '2026-08-22T00:00:00Z', quote_volume: quoteVolume } as Ticker24h
}

describe('volatilityTop', () => {
  it('ordena por ATR relativo decrescente e converte para %', () => {
    const rows = volatilityTop([
      { symbol: 'AAA', feature: feature(2), lastClose: 100, changePercent: 1.5 }, // 2 %
      { symbol: 'BBB', feature: feature(5), lastClose: 100, changePercent: -2 }, // 5 %
      { symbol: 'CCC', feature: feature(1), lastClose: 10, changePercent: null }, // 10 %
    ])
    expect(rows.map(r => r.symbol)).toEqual(['CCC', 'BBB', 'AAA'])
    expect(rows[0]?.value).toBeCloseTo(10)
    expect(rows[2]?.delta).toBe(1.5)
  })

  it('descarta linhas sem ATR ou sem preço de fechamento', () => {
    const rows = volatilityTop([
      { symbol: 'AAA', feature: feature(null), lastClose: 100, changePercent: null },
      { symbol: 'BBB', feature: null, lastClose: 100, changePercent: null },
      { symbol: 'CCC', feature: feature(2), lastClose: null, changePercent: null },
      { symbol: 'DDD', feature: feature(2), lastClose: 0, changePercent: null },
    ])
    expect(rows).toEqual([])
  })

  it('respeita o limite (top 5)', () => {
    const input = Array.from({ length: 8 }, (_, i) => ({
      symbol: `S${i}`,
      feature: feature(i + 1),
      lastClose: 100,
      changePercent: null,
    }))
    expect(volatilityTop(input)).toHaveLength(5)
  })
})

describe('volumeTop', () => {
  const days = (volumes: number[]) =>
    volumes.map((v, i) => kline(`2026-08-${22 - i}T00:00:00Z`, v))

  it('compara o volume 24h com a média dos 7 dias anteriores (sem a vela aberta)', () => {
    // Vela aberta (mais nova) = 999 é descartada; média dos 3 dias anteriores = 100.
    const rows = volumeTop([
      { ticker: ticker('AAA', 150), dailyKlines: days([999, 100, 100, 100]) },
    ])
    expect(rows[0]?.value).toBe(150)
    expect(rows[0]?.delta).toBeCloseTo(50)
  })

  it('histórico com menos de 3 dias fechados → delta null', () => {
    const rows = volumeTop([
      { ticker: ticker('AAA', 150), dailyKlines: days([999, 100]) },
    ])
    expect(rows[0]?.delta).toBeNull()
  })

  it('ordena por volume decrescente e ignora tickers sem volume', () => {
    const rows = volumeTop([
      { ticker: ticker('AAA', 100), dailyKlines: [] },
      { ticker: ticker('BBB', null), dailyKlines: [] },
      { ticker: ticker('CCC', 300), dailyKlines: [] },
    ])
    expect(rows.map(r => r.symbol)).toEqual(['CCC', 'AAA'])
  })
})

describe('splitReading', () => {
  it('separa a primeira frase como manchete', () => {
    const parts = splitReading('Hoje, o mercado abriu comprador. 14 dos 20 ativos subiram nas últimas 24 h.')
    expect(parts).toEqual({
      headline: 'Hoje, o mercado abriu comprador.',
      body: '14 dos 20 ativos subiram nas últimas 24 h.',
    })
  })

  it('texto de uma frase só vira manchete sem corpo', () => {
    expect(splitReading('O mercado abriu comprador.')).toEqual({
      headline: 'O mercado abriu comprador.',
      body: '',
    })
  })

  it('manchete longa demais desce inteira para o corpo', () => {
    const long = `${'a'.repeat(120)}. Segunda frase.`
    const parts = splitReading(long)
    expect(parts?.headline).toBe('')
    expect(parts?.body).toContain('Segunda frase.')
  })

  it('devolve null sem texto', () => {
    expect(splitReading(null)).toBeNull()
    expect(splitReading('   ')).toBeNull()
  })

  it('normaliza espaços e quebras de linha', () => {
    expect(splitReading('Primeira.\n\n   Segunda   frase.')).toEqual({
      headline: 'Primeira.',
      body: 'Segunda frase.',
    })
  })
})

describe('splitReading · tipografia', () => {
  it('mantém numeral e símbolo de porcentagem na mesma linha', () => {
    const parts = splitReading('Alta média de 1,4 % nos 20 ativos. Segunda frase.')
    expect(parts?.headline).toBe('Alta média de 1,4\u00A0% nos 20 ativos.')
  })
})
