import type { ForecastRound, MonteCarloSeries, ScenarioRow } from '~/types/forecast'

/**
 * Previsões do modelo (Design.md §11).
 *
 * O contrato da API (`front-end/openapi/openapi.json`) **ainda não expõe**
 * `/api/v1/forecasts`: chamar um endpoint inexistente seria inventar contrato.
 * Enquanto o marco de ML não sai, este composable devolve o estado vazio
 * honesto — sem requisição, sem número fabricado, sem trajetória desenhada.
 *
 * Quando o endpoint entrar no contrato e `pnpm api:types` regerar os tipos,
 * troque o corpo por `useAsyncData(... api.get('/api/v1/forecasts') ...)` e
 * mapeie a resposta para `ForecastRound` / `ScenarioRow` / `MonteCarloSeries`.
 * Nenhum componente desta tela precisa mudar: todos já leem só props tipadas.
 */

export interface ForecastsState {
  round: Ref<ForecastRound | null>
  rows: Ref<ScenarioRow[]>
  /** `true` quando a API de forecasts ainda não faz parte do contrato. */
  unavailable: Ref<boolean>
  refresh: () => Promise<void>
}

export function useForecasts(): ForecastsState {
  const round = ref<ForecastRound | null>(null)
  const rows = ref<ScenarioRow[]>([])
  const unavailable = ref(true)

  return {
    round,
    rows,
    unavailable,
    refresh: async () => {},
  }
}

export interface MonteCarloState {
  series: Ref<MonteCarloSeries | null>
  unavailable: Ref<boolean>
  /** Reinicia a animação com as mesmas trajetórias (nunca gera novas). */
  restart: () => void
  restartToken: Ref<number>
}

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
