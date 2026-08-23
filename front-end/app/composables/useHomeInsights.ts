import type { FeatureRow, Kline } from '~/types/api'
import { volatilityTop, volumeTop, type InsightRow } from '~/utils/insights'
import { sortTickers } from '~/utils/tickers'

interface SymbolBundle {
  symbol: string
  dailyKlines: Kline[]
  feature: FeatureRow | null
}

async function chunked<T, R>(items: T[], size: number, run: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = []
  for (let i = 0; i < items.length; i += size) {
    out.push(...await Promise.all(items.slice(i, i + size).map(run)))
  }
  return out
}

/**
 * Rankings do Início: 1 chamada de tickers + klines/features 1d por símbolo com
 * concorrência limitada (top 20 → ~40 chamadas leves na primeira carga, depois
 * cache de sessão do useAsyncData). Candidato a endpoint agregado no back-end
 * quando o serviço de insights (fase 6) crescer.
 */
export function useHomeInsights() {
  const api = useApi()
  const tickers = useTickers24h()

  const bundles = useAsyncData<SymbolBundle[]>(
    'home-insights',
    async () => {
      const list = sortTickers(tickers.data.value, 'quote_volume', 'desc')
      if (!list.length) return []
      return chunked(list.map(t => t.symbol), 6, async (symbol) => {
        const [klines, features] = await Promise.all([
          api.get('/api/v1/klines/{timeframe}', { params: { path: { timeframe: '1d' }, query: { symbol, limit: 9 } } }).catch(() => [] as Kline[]),
          api.get('/api/v1/features/{timeframe}', { params: { path: { timeframe: '1d' }, query: { symbol, limit: 1 } } }).catch(() => [] as FeatureRow[]),
        ])
        return { symbol, dailyKlines: [...klines], feature: features[0] ?? null }
      })
    },
    { default: () => [], watch: [tickers.data] },
  )

  const bySymbol = computed(() => new Map(bundles.data.value.map(b => [b.symbol, b])))

  const volatility = computed<InsightRow[]>(() => volatilityTop(
    bundles.data.value.map((b) => {
      const ticker = tickers.data.value.find(t => t.symbol === b.symbol)
      const newest = [...b.dailyKlines].sort((a, k) => Date.parse(k.open_time) - Date.parse(a.open_time))[0]
      return {
        symbol: b.symbol,
        feature: b.feature,
        lastClose: ticker?.last_price ?? newest?.close ?? null,
        changePercent: ticker?.price_change_percent ?? null,
      }
    }),
  ))

  const volume = computed<InsightRow[]>(() => volumeTop(
    tickers.data.value
      .map(ticker => ({ ticker, dailyKlines: bySymbol.value.get(ticker.symbol)?.dailyKlines ?? [] }))
      .filter(r => r.dailyKlines.length > 0 || r.ticker.quote_volume != null),
  ))

  const status = computed(() => {
    if (tickers.status.value === 'error' && !tickers.data.value.length) return 'error' as const
    if (bundles.status.value === 'success' && bundles.data.value.length) return 'success' as const
    if (tickers.status.value === 'pending' || bundles.status.value === 'pending' || bundles.status.value === 'idle') return 'pending' as const
    return bundles.status.value === 'error' ? 'error' as const : 'success' as const
  })

  async function refresh() {
    await tickers.refresh()
    await bundles.refresh()
  }

  return { tickers, volatility, volume, status, refresh }
}
