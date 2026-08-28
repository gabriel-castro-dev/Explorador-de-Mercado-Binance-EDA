import type { MaybeRefOrGetter } from 'vue'
import type { ForecastMetrics, ForecastPoint, MonteCarloSeriesOut } from '~/types/api'
import type { ForecastRound, MonteCarloSeries, ScenarioRow } from '~/types/forecast'
import type { AsyncStatus } from '~/utils/async-state'
import type { InsightRow } from '~/utils/insights'
import { unwrapApiError } from '~/utils/api-errors'
import { buildRound, gapTop, mapMonteCarlo, mapScenarioRows } from '~/utils/forecast-mapping'

/**
 * Previsões do modelo (Design.md §11): `GET /api/v1/forecasts` devolve a curva
 * 1–7 dias do run mais recente por ativo; `/forecasts/metrics` traz MAE, acerto
 * de direção e confiança da mesma versão; o preço atual vem dos tickers 24h.
 * O mapeamento para a UI é puro (`utils/forecast-mapping.ts`).
 */

/** Métricas da versão vigente; `null` sem rodada publicada. */
export function useForecastMetrics() {
  const api = useApi()
  return useAsyncData<ForecastMetrics | null>('forecast-metrics', () => api.get('/api/v1/forecasts/metrics'), {
    default: () => null,
  })
}

export interface ForecastsState {
  round: ComputedRef<ForecastRound | null>
  rows: ComputedRef<ScenarioRow[]>
  /** Linhas da faixa "Gap real × projeção" do Início. */
  gap: ComputedRef<InsightRow[]>
  status: ComputedRef<AsyncStatus>
  refresh: () => Promise<void>
}

export function useForecasts(): ForecastsState {
  const api = useApi()
  const tickers = useTickers24h()
  const metrics = useForecastMetrics()
  const points = useAsyncData<ForecastPoint[]>('forecasts', () => api.get('/api/v1/forecasts'), {
    default: () => [],
  })

  const rows = computed(() => mapScenarioRows(points.data.value, tickers.data.value, metrics.data.value))
  const round = computed(() => buildRound(points.data.value, rows.value, metrics.data.value))
  const gap = computed(() => gapTop(rows.value))
  const status = computed<AsyncStatus>(() => points.status.value)

  return {
    round,
    rows,
    gap,
    status,
    refresh: async () => {
      await Promise.all([points.refresh(), tickers.refresh(), metrics.refresh()])
    },
  }
}

export interface MonteCarloState {
  series: ComputedRef<MonteCarloSeries | null>
  status: ComputedRef<AsyncStatus>
  /** A API respondeu 404: não há nuvem para este ativo na rodada vigente. */
  notFound: ComputedRef<boolean>
  /** Reinicia a animação com as mesmas trajetórias (nunca gera novas). */
  restart: () => void
  restartToken: Ref<number>
  refresh: () => Promise<void>
}

/**
 * Nuvem Monte Carlo de um ativo: `GET /api/v1/forecasts/monte-carlo?symbol=`.
 * Chave reativa pelo símbolo; 404 vira `series = null` com `notFound = true`
 * (estado vazio honesto), outros erros ficam em `status = 'error'`.
 * O front nunca gera trajetórias — só desenha as recebidas.
 */
export function useMonteCarlo(symbol: MaybeRefOrGetter<string | null>): MonteCarloState {
  const api = useApi()
  const key = computed(() => `monte-carlo:${toValue(symbol) ?? ''}`)
  const notFound = ref(false)
  const restartToken = ref(0)

  const raw = useAsyncData<MonteCarloSeriesOut | null>(
    key,
    async () => {
      notFound.value = false
      const s = toValue(symbol)
      if (!s) return null
      try {
        return await api.get('/api/v1/forecasts/monte-carlo', { params: { query: { symbol: s } } })
      } catch (error) {
        if (unwrapApiError(error)?.status === 404) {
          notFound.value = true
          return null
        }
        throw error
      }
    },
    { default: () => null, watch: [key] },
  )

  const series = computed(() => (raw.data.value ? mapMonteCarlo(raw.data.value) : null))
  const status = computed<AsyncStatus>(() => raw.status.value)

  return {
    series,
    status,
    notFound: computed(() => notFound.value),
    restart: () => {
      restartToken.value += 1
    },
    restartToken,
    refresh: async () => {
      await raw.refresh()
    },
  }
}
