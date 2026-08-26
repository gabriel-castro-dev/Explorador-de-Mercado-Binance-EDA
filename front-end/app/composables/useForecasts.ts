import type { ForecastPoint } from '~/types/api'
import type { ForecastRound, MonteCarloSeries, ScenarioRow } from '~/types/forecast'
import type { AsyncStatus } from '~/utils/async-state'
import type { InsightRow } from '~/utils/insights'
import { buildRound, gapTop, mapScenarioRows } from '~/utils/forecast-mapping'

/**
 * Previsões do modelo (Design.md §11): `GET /api/v1/forecasts` devolve a curva
 * 1–7 dias do run mais recente por ativo; o preço atual vem dos tickers 24h.
 * O mapeamento para a UI é puro (`utils/forecast-mapping.ts`).
 */

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
  const points = useAsyncData<ForecastPoint[]>('forecasts', () => api.get('/api/v1/forecasts'), {
    default: () => [],
  })

  const rows = computed(() => mapScenarioRows(points.data.value, tickers.data.value))
  const round = computed(() => buildRound(points.data.value, rows.value))
  const gap = computed(() => gapTop(rows.value))
  const status = computed<AsyncStatus>(() => points.status.value)

  return {
    round,
    rows,
    gap,
    status,
    refresh: async () => {
      await Promise.all([points.refresh(), tickers.refresh()])
    },
  }
}

export interface MonteCarloState {
  series: Ref<MonteCarloSeries | null>
  unavailable: Ref<boolean>
  /** Reinicia a animação com as mesmas trajetórias (nunca gera novas). */
  restart: () => void
  restartToken: Ref<number>
}

/**
 * A API ainda não expõe trajetórias simuladas (só `pred_lower`/`pred_upper` por
 * horizonte). Enquanto `/api/v1/forecasts/monte-carlo` não entra no contrato,
 * o estado é vazio e honesto — o front nunca gera trajetórias.
 * Roadmap: docs/ml/2026-08-26-handoff-backend-forecasts.md §4.
 */
export function useMonteCarlo(): MonteCarloState {
  const series = ref<MonteCarloSeries | null>(null)
  const unavailable = ref(true)
  const restartToken = ref(0)

  return {
    series,
    unavailable,
    restart: () => {
      restartToken.value += 1
    },
    restartToken,
  }
}
