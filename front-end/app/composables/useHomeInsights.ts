import type { FeatureRow, Kline } from '~/types/api'
import { volatilityTop, volumeTop, type InsightRow } from '~/utils/insights'
import { sortTickers } from '~/utils/tickers'

interface SymbolBundle {
  symbol: string
  dailyKlines: Kline[]
  feature: FeatureRow | null
}

type BundleStatus = 'idle' | 'pending' | 'success' | 'error'

async function chunked<T, R>(items: T[], size: number, run: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = []
  for (let i = 0; i < items.length; i += size) {
    out.push(...await Promise.all(items.slice(i, i + size).map(run)))
  }
  return out
}

/**
 * Rankings do Início: 1 chamada de tickers + klines/features 1d por símbolo com
 * concorrência limitada (top 20 → ~40 chamadas leves), disparadas quando a lista
 * de tickers chega. Estado em useState (sobrevive a navegações na sessão).
 * Candidato a endpoint agregado no back-end quando o serviço de insights crescer.
 */
export function useHomeInsights() {
  const api = useApi()
  const tickers = useTickers24h()

  const bundles = useState<SymbolBundle[]>('home-insights-bundles', () => [])
  const bundleStatus = useState<BundleStatus>('home-insights-status', () => 'idle')

  async function loadBundles() {
    const list = sortTickers(tickers.data.value, 'quote_volume', 'desc')
    if (!list.length) return
    bundleStatus.value = 'pending'
    try {
      bundles.value = await chunked(list.map(t => t.symbol), 6, async (symbol) => {
        const [klines, features] = await Promise.all([
          api.get('/api/v1/klines/{timeframe}', { params: { path: { timeframe: '1d' }, query: { symbol, limit: 9 } } }).catch(() => [] as Kline[]),
          api.get('/api/v1/features/{timeframe}', { params: { path: { timeframe: '1d' }, query: { symbol, limit: 1 } } }).catch(() => [] as FeatureRow[]),
        ])
        return { symbol, dailyKlines: [...klines], feature: features[0] ?? null }
      })
      bundleStatus.value = 'success'
    } catch {
      bundleStatus.value = 'error'
    }
  }

  // Dispara quando os tickers chegam (e uma vez por sessão; refresh() refaz).
  watch(() => tickers.data.value.length, (n) => {
    if (n && bundleStatus.value === 'idle') void loadBundles()
  }, { immediate: true })

  const bySymbol = computed(() => new Map(bundles.value.map(b => [b.symbol, b])))

  const volatility = computed<InsightRow[]>(() => volatilityTop(
    bundles.value.map((b) => {
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

  const status = computed<BundleStatus>(() => {
    if (tickers.status.value === 'error' && !tickers.data.value.length) return 'error'
    if (bundleStatus.value === 'success') return 'success'
    if (tickers.status.value === 'pending' || bundleStatus.value === 'pending' || bundleStatus.value === 'idle') return 'pending'
    return bundleStatus.value
  })

  async function refresh() {
    await tickers.refresh()
    await loadBundles()
  }

  return { tickers, volatility, volume, status, refresh }
}
