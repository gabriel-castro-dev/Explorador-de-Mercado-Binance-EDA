import type { ForecastMetrics, ForecastPoint, MonteCarloSeriesOut, Ticker24h } from '~/types/api'
import type { ForecastRound, HorizonSummary, MonteCarloSeries, ScenarioCell, ScenarioRow } from '~/types/forecast'
import type { InsightRow } from '~/utils/insights'
import { formatPercent, formatUtc } from '~/utils/format'

/**
 * Mapeia a resposta plana de `GET /api/v1/forecasts` (símbolo × alvo × horizonte)
 * para o contrato da UI (Design.md §11).
 *
 * Regra dura: nada aqui cria valor financeiro. Toda célula é a previsão recebida
 * ou aritmética sobre ela (variação contra o preço atual, média entre ativos).
 * Horizontes que o modelo não publica (mensal, anual — ADR-0004) ficam `null`.
 */

export const FORECAST_DISCLAIMER = 'Leia as previsões como cenários, não como recomendação de compra ou venda.'

/** Horizontes publicados pelo modelo (1–7 dias) que a UI expõe. */
const HORIZON_DAYS = { daily: 1, weekly: 7 } as const

const EMPTY_CELL: ScenarioCell = { price: null, changePercent: null }

/**
 * Variação % da previsão contra o preço atual do ticker. Sem ticker, cai para o
 * retorno previsto pelo modelo (relativo ao último fechamento que ele observou).
 */
function changePercent(point: ForecastPoint, realPrice: number | null): number | null {
  if (realPrice !== null && realPrice > 0) return (point.predicted_close / realPrice - 1) * 100
  return Number.isFinite(point.predicted_log_return) ? Math.expm1(point.predicted_log_return) * 100 : null
}

function cellOf(point: ForecastPoint | undefined, realPrice: number | null): ScenarioCell {
  if (!point) return EMPTY_CELL
  return { price: point.predicted_close, changePercent: changePercent(point, realPrice) }
}

/**
 * Métricas só valem para a mesma `model_version` das previsões: uma rodada
 * publicada entre as duas requisições não pode misturar números.
 */
function metricsFor(points: readonly ForecastPoint[], metrics: ForecastMetrics | null | undefined): ForecastMetrics | null {
  const version = points[0]?.model_version
  if (!metrics || !version || metrics.model_version !== version) return null
  return metrics
}

/** Uma linha por símbolo, na ordem em que a API os devolve (alfabética). */
export function mapScenarioRows(
  points: readonly ForecastPoint[],
  tickers: readonly Ticker24h[],
  metrics: ForecastMetrics | null = null,
): ScenarioRow[] {
  const usable = metricsFor(points, metrics)
  const priceBySymbol = new Map(tickers.map(t => [t.symbol, t.last_price ?? null]))
  const bySymbol = new Map<string, Map<number, ForecastPoint>>()
  for (const point of points) {
    let horizons = bySymbol.get(point.symbol)
    if (!horizons) {
      horizons = new Map()
      bySymbol.set(point.symbol, horizons)
    }
    horizons.set(point.horizon_days, point)
  }

  return [...bySymbol.entries()].map(([symbol, horizons]) => {
    const realPrice = priceBySymbol.get(symbol) ?? null
    return {
      symbol,
      realPrice,
      daily: cellOf(horizons.get(HORIZON_DAYS.daily), realPrice),
      weekly: cellOf(horizons.get(HORIZON_DAYS.weekly), realPrice),
      monthly: EMPTY_CELL,
      yearly: EMPTY_CELL,
      // Confiança = acerto de direção em 1 dia (0–100), definida pela API; null com histórico curto.
      confidence: usable?.per_symbol[symbol]?.confidence ?? null,
    }
  })
}

function mean(values: readonly (number | null)[]): number | null {
  const finite = values.filter((v): v is number => v !== null && Number.isFinite(v))
  if (!finite.length) return null
  return finite.reduce((sum, v) => sum + v, 0) / finite.length
}

/**
 * Cabeçalho da rodada. `null` sem previsões. MAE e acerto de direção vêm de
 * `/forecasts/metrics` (horizonte de 1 dia) quando a versão coincide; senão `null`.
 */
export function buildRound(
  points: readonly ForecastPoint[],
  rows: readonly ScenarioRow[],
  metrics: ForecastMetrics | null = null,
): ForecastRound | null {
  const first = points[0]
  if (!first) return null
  const usable = metricsFor(points, metrics)
  const h1 = usable?.per_horizon.y_1

  const isFallback = points.some(p => p.is_fallback)
  const daily = mean(rows.map(r => r.daily.changePercent))
  const weekly = mean(rows.map(r => r.weekly.changePercent))
  const horizons: HorizonSummary[] = [
    { key: 'daily', changePercent: daily },
    { key: 'weekly', changePercent: weekly },
    { key: 'monthly', changePercent: null },
    { key: 'yearly', changePercent: null },
  ]

  const runAt = points.reduce((latest, p) => (p.run_at > latest ? p.run_at : latest), first.run_at)

  return {
    model: usable?.model_type ?? first.model_type ?? 'Global',
    version: first.model_version,
    status: isFallback ? 'FALLBACK NAIVE' : 'EM VALIDAÇÃO',
    generatedAt: runAt,
    maePercent: h1 ? h1.mae_log_return * 100 : null,
    directionAccuracy: h1?.dir_acc == null ? null : h1.dir_acc * 100,
    horizons,
    narrative: buildNarrative(rows.length, runAt, daily, weekly, isFallback),
    disclaimer: FORECAST_DISCLAIMER,
  }
}

/** Resumo determinístico da rodada: só contagens e médias das previsões reais. */
export function buildNarrative(
  symbols: number,
  runAt: string,
  daily: number | null,
  weekly: number | null,
  isFallback: boolean,
): string {
  const headline = `${symbols} ${symbols === 1 ? 'ativo projetado' : 'ativos projetados'} de 1 a 7 dias.`
  const averages = daily === null && weekly === null
    ? 'Ainda sem base de preço atual para calcular a variação média.'
    : `Em média, o modelo aponta ${formatPercent(daily, 1)} em 1 dia e ${formatPercent(weekly, 1)} em 7 dias sobre o preço atual.`
  const tail = isFallback
    ? 'O campeão não bateu o naive na validação: esta curva é o fallback ingênuo, marcado como tal.'
    : 'As faixas de incerteza alargam com o horizonte, como quantis do erro de validação.'
  return `${headline} Rodada de ${formatUtc(runAt)}. ${averages} ${tail}`
}

/**
 * Faixa "Gap real × projeção" do Início: variação diária prevista por ativo,
 * maiores magnitudes primeiro. Só entra quem tem preço atual — sem ele não há gap.
 */
export function gapTop(rows: readonly ScenarioRow[], limit = 5): InsightRow[] {
  return rows
    .filter(r => r.realPrice !== null && r.daily.changePercent !== null)
    .map(r => ({ symbol: r.symbol, value: r.daily.changePercent as number, delta: null }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, limit)
}

/**
 * `/forecasts/monte-carlo` já vem no formato da UI; só normaliza `classified`
 * (`null` da API vira ausente) e ordena o observado. Trajetórias são as reais.
 */
export function mapMonteCarlo(out: MonteCarloSeriesOut): MonteCarloSeries {
  const c = out.classified
  const classified = c
    ? {
        best: c.best ?? undefined,
        base: c.base ?? undefined,
        worst: c.worst ?? undefined,
      }
    : undefined
  return {
    symbol: out.symbol,
    horizonDays: out.horizonDays,
    observed: [...out.observed].sort((a, b) => a.time - b.time),
    stepSeconds: out.stepSeconds,
    paths: out.paths,
    simulatedCount: out.simulatedCount,
    classified,
  }
}
