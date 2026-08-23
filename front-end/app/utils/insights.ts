import type { FeatureRow, Kline, Ticker24h } from '~/types/api'

/**
 * Rankings do Início (Design.md §5): funções puras sobre dados já carregados.
 * O card de gap real × projeção fica de fora — depende da API de forecasts (marco 3).
 */

export interface InsightRow {
  symbol: string
  /** Valor principal formatável (ex.: ATR relativo, volume 24h). */
  value: number
  /** Variação de apoio (ex.: variação 24h, % vs média 7d); null quando não há base. */
  delta: number | null
}

/** ATR 14 relativo (`atr_14 / close` da última vela 1d), decrescente. */
export function volatilityTop(
  rows: { symbol: string, feature: FeatureRow | null, lastClose: number | null, changePercent: number | null }[],
  limit = 5,
): InsightRow[] {
  const out: InsightRow[] = []
  for (const r of rows) {
    const atr = r.feature?.atr_14 ?? null
    if (atr === null || r.lastClose === null || r.lastClose <= 0) continue
    out.push({ symbol: r.symbol, value: (atr / r.lastClose) * 100, delta: r.changePercent })
  }
  return out.sort((a, b) => b.value - a.value).slice(0, limit)
}

/**
 * Volume 24h (ticker) vs média dos 7 dias anteriores (klines 1d, excluindo a
 * vela aberta). `delta` = % acima/abaixo da média; null com histórico < 3 dias.
 */
export function volumeTop(
  rows: { ticker: Ticker24h, dailyKlines: readonly Kline[] }[],
  limit = 5,
): InsightRow[] {
  const out: InsightRow[] = []
  for (const { ticker, dailyKlines } of rows) {
    const volume = ticker.quote_volume ?? null
    if (volume === null) continue
    // Ordena do mais novo ao mais antigo, descarta a vela aberta (a mais nova) e pega 7.
    const history = [...dailyKlines]
      .sort((a, b) => Date.parse(b.open_time) - Date.parse(a.open_time))
      .slice(1, 8)
      .map(k => k.quote_asset_volume)
      .filter((v): v is number => typeof v === 'number' && v > 0)
    const mean = history.length >= 3 ? history.reduce((s, v) => s + v, 0) / history.length : null
    out.push({ symbol: ticker.symbol, value: volume, delta: mean ? ((volume - mean) / mean) * 100 : null })
  }
  return out.sort((a, b) => b.value - a.value).slice(0, limit)
}
