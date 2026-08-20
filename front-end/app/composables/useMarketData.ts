import type { MaybeRefOrGetter } from 'vue'
import type { FeatureRow, Kline, SymbolRow, Ticker24h, Timeframe } from '~/types/api'
import { LIMIT_BY_TF } from '~/utils/constants'

/**
 * Leituras da API via useAsyncData com chaves reativas (refetch automático ao mudar símbolo/tf).
 * Todas devolvem `[]` por padrão; erros ficam em `error` (ApiError normalizado pelo useApi).
 */

export function useSymbols() {
  const api = useApi()
  return useAsyncData<SymbolRow[]>('symbols', () => api.get('/api/v1/symbols'), {
    default: () => [],
  })
}

export function useKlines(symbol: MaybeRefOrGetter<string | null>, tf: MaybeRefOrGetter<Timeframe>, opts: { end?: MaybeRefOrGetter<string | undefined> } = {}) {
  const api = useApi()
  const key = computed(() => `klines:${toValue(tf)}:${toValue(symbol) ?? ''}:${toValue(opts.end) ?? ''}`)
  return useAsyncData<Kline[]>(
    key,
    () => {
      const s = toValue(symbol)
      if (!s) return Promise.resolve([])
      const timeframe = toValue(tf)
      return api.get('/api/v1/klines/{timeframe}', {
        params: { path: { timeframe }, query: { symbol: s, limit: LIMIT_BY_TF[timeframe], end: toValue(opts.end) ?? undefined } },
      })
    },
    { default: () => [], watch: [key] },
  )
}

export function useFeatures(symbol: MaybeRefOrGetter<string | null>, tf: MaybeRefOrGetter<Timeframe>, opts: { end?: MaybeRefOrGetter<string | undefined> } = {}) {
  const api = useApi()
  const key = computed(() => `features:${toValue(tf)}:${toValue(symbol) ?? ''}:${toValue(opts.end) ?? ''}`)
  return useAsyncData<FeatureRow[]>(
    key,
    () => {
      const s = toValue(symbol)
      if (!s) return Promise.resolve([])
      const timeframe = toValue(tf)
      return api.get('/api/v1/features/{timeframe}', {
        params: { path: { timeframe }, query: { symbol: s, limit: LIMIT_BY_TF[timeframe], end: toValue(opts.end) ?? undefined } },
      })
    },
    { default: () => [], watch: [key] },
  )
}

/** Último snapshot 24h de todos os ativos (um fetch; filtragem/ordenação no cliente). */
export function useTickers24h() {
  const api = useApi()
  return useAsyncData<Ticker24h[]>('tickers24h', () => api.get('/api/v1/tickers/24h'), {
    default: () => [],
  })
}

/** Snapshot 24h de um único ativo, derivado da lista (evita requisição extra). */
export function useTicker24h(symbol: MaybeRefOrGetter<string | null>) {
  const list = useTickers24h()
  const ticker = computed<Ticker24h | null>(() => {
    const s = toValue(symbol)
    if (!s) return null
    return list.data.value.find(t => t.symbol === s) ?? null
  })
  return { ...list, ticker }
}
