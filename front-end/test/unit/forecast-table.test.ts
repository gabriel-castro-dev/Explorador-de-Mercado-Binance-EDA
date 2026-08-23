import { describe, expect, it } from 'vitest'
import { scenarioSortValue, sortScenarioRows } from '../../app/utils/forecast-table'
import type { ScenarioRow } from '../../app/types/forecast'

function row(symbol: string, confidence: number | null, dailyPct: number | null): ScenarioRow {
  const cell = { price: null, changePercent: dailyPct }
  return {
    symbol,
    realPrice: 100,
    daily: cell,
    weekly: cell,
    monthly: cell,
    yearly: cell,
    confidence,
  }
}

describe('scenarioSortValue', () => {
  it('compara horizontes pela variação percentual', () => {
    expect(scenarioSortValue(row('BTCUSDT', 80, 1.2), 'daily')).toBe(1.2)
  })

  it('compara ativo pelo símbolo', () => {
    expect(scenarioSortValue(row('BTCUSDT', 80, 1.2), 'symbol')).toBe('BTCUSDT')
  })
})

describe('sortScenarioRows', () => {
  const rows = [row('AAA', 60, -1), row('BBB', null, 3), row('CCC', 90, 2)]

  it('ordena por confiança decrescente com nulls no fim', () => {
    expect(sortScenarioRows(rows, 'confidence', 'desc').map(r => r.symbol)).toEqual(['CCC', 'AAA', 'BBB'])
  })

  it('mantém nulls no fim também na ordem crescente', () => {
    expect(sortScenarioRows(rows, 'confidence', 'asc').map(r => r.symbol)).toEqual(['AAA', 'CCC', 'BBB'])
  })

  it('ordena por horizonte diário', () => {
    expect(sortScenarioRows(rows, 'daily', 'desc').map(r => r.symbol)).toEqual(['BBB', 'CCC', 'AAA'])
  })

  it('não muta o array original', () => {
    const original = [...rows]
    sortScenarioRows(rows, 'symbol', 'asc')
    expect(rows).toEqual(original)
  })
})
