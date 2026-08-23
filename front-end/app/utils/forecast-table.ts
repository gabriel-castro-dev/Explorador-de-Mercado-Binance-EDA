import type { ScenarioRow } from '~/types/forecast'
import type { SortDir } from '~/utils/tickers'

/** Ordenação da tabela de cenários (Design.md §11.2). Puras e testáveis. */

export type ScenarioSortKey = 'symbol' | 'realPrice' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'confidence'

/** Valor comparável de uma coluna; horizontes comparam pela variação %. */
export function scenarioSortValue(row: ScenarioRow, key: ScenarioSortKey): number | string | null {
  switch (key) {
    case 'symbol': return row.symbol
    case 'realPrice': return row.realPrice
    case 'confidence': return row.confidence
    default: return row[key].changePercent
  }
}

/** Ordena uma cópia; `null` fica sempre por último, independente da direção. */
export function sortScenarioRows(
  rows: readonly ScenarioRow[],
  key: ScenarioSortKey,
  dir: SortDir = 'desc',
): ScenarioRow[] {
  const factor = dir === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    const av = scenarioSortValue(a, key)
    const bv = scenarioSortValue(b, key)
    const aNull = av === null || av === undefined
    const bNull = bv === null || bv === undefined
    if (aNull && bNull) return a.symbol.localeCompare(b.symbol)
    if (aNull) return 1
    if (bNull) return -1
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * factor
    return String(av).localeCompare(String(bv)) * factor
  })
}
