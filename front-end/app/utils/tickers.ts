import type { Ticker24h } from '~/types/api'

export type TickerSortKey = keyof Ticker24h
export type SortDir = 'asc' | 'desc'

/** Ordena cópia; nulls sempre por último, independente da direção (ux-spec §5). */
export function sortTickers(rows: readonly Ticker24h[], key: TickerSortKey, dir: SortDir = 'desc'): Ticker24h[] {
  const factor = dir === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    const av = a[key]
    const bv = b[key]
    const aNull = av === null || av === undefined
    const bNull = bv === null || bv === undefined
    if (aNull && bNull) return a.symbol.localeCompare(b.symbol)
    if (aNull) return 1
    if (bNull) return -1
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * factor
    return String(av).localeCompare(String(bv)) * factor
  })
}

/** Filtro por símbolo ou nome legível (case-insensitive). */
export function filterTickers(rows: readonly Ticker24h[], query: string, nameOf: (symbol: string) => string | undefined): Ticker24h[] {
  const q = query.trim().toLowerCase()
  if (!q) return [...rows]
  return rows.filter((r) => {
    if (r.symbol.toLowerCase().includes(q)) return true
    const name = nameOf(r.symbol)
    return name ? name.toLowerCase().includes(q) : false
  })
}

/** Snapshot mais recente entre as linhas (para o selo do resumo 24h). */
export function latestSnapshotAt(rows: readonly Ticker24h[]): string | null {
  let best: string | null = null
  let bestT = -Infinity
  for (const r of rows) {
    const iso = r.close_time ?? r.open_time
    const t = Date.parse(iso)
    if (t > bestT) {
      bestT = t
      best = iso
    }
  }
  return best
}

/** Spread relativo bid/ask em % (null se faltar dado ou bid=0). */
export function spreadPercent(t: Pick<Ticker24h, 'bid_price' | 'ask_price'>): number | null {
  if (t.bid_price == null || t.ask_price == null || t.bid_price === 0) return null
  return ((t.ask_price - t.bid_price) / t.bid_price) * 100
}

/** Um ticker "sem dados": todos os campos numéricos relevantes nulos. */
export function tickerHasData(t: Ticker24h): boolean {
  return t.last_price != null || t.quote_volume != null || t.price_change_percent != null
}
