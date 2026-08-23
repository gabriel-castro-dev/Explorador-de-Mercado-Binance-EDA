/**
 * Contrato de previsões consumido pela UI (Design.md §11).
 *
 * A API de forecasts ainda **não existe** em `openapi/openapi.json` — estes tipos
 * descrevem o que a tela precisa receber, não um endpoint publicado. Nada aqui
 * gera número: os componentes só desenham o que chega por props.
 * Ver `useForecasts()` para o estado vazio honesto enquanto o marco de ML não sai.
 */

export type HorizonKey = 'daily' | 'weekly' | 'monthly' | 'yearly'

export const HORIZONS: readonly { key: HorizonKey, label: string }[] = [
  { key: 'daily', label: 'DIÁRIO' },
  { key: 'weekly', label: 'SEMANAL' },
  { key: 'monthly', label: 'MENSAL' },
  { key: 'yearly', label: 'ANUAL' },
] as const

export interface HorizonSummary {
  key: HorizonKey
  /** Variação média projetada, em %. `null` = sem rodada publicada. */
  changePercent: number | null
}

/** Cabeçalho da rodada: versão, MAE e acerto de direção (faixa tipográfica). */
export interface ForecastRound {
  model: string
  version: string
  /** Ex.: `EM VALIDAÇÃO`. */
  status: string
  generatedAt: string
  maeUsdt: number | null
  directionAccuracy: number | null
  horizons: readonly HorizonSummary[]
  /** Texto do resumo da rodada; `null` enquanto não houver. */
  narrative: string | null
  disclaimer: string
}

export interface ScenarioCell {
  price: number | null
  changePercent: number | null
}

export interface ScenarioRow {
  symbol: string
  realPrice: number | null
  daily: ScenarioCell
  weekly: ScenarioCell
  monthly: ScenarioCell
  yearly: ScenarioCell
  /** Confiança do backtesting, 0–100. */
  confidence: number | null
}

export interface ObservedPoint {
  /** Segundos UTC. */
  time: number
  value: number
}

/**
 * Entrada do Monte Carlo. `paths` são trajetórias **reais** recebidas do modelo;
 * `simulatedCount` é quanto foi de fato simulado (a UI pode desenhar uma amostra
 * e informa a quantidade real — Design.md §11.3).
 */
export interface MonteCarloSeries {
  symbol: string
  horizonDays: number
  observed: readonly ObservedPoint[]
  /** Intervalo entre passos previstos, em segundos. */
  stepSeconds: number
  /** Cada trajetória: valores por passo, começando na linha de corte. */
  paths: readonly (readonly number[])[]
  simulatedCount: number
  /** Índices classificados pela API, quando ela classifica. */
  classified?: { best?: number, base?: number, worst?: number }
}
