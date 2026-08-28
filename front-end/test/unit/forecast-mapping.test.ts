import { describe, expect, it } from 'vitest'
import { buildNarrative, buildRound, gapTop, mapMonteCarlo, mapScenarioRows } from '../../app/utils/forecast-mapping'
import type { ForecastMetrics, ForecastPoint, MonteCarloSeriesOut, Ticker24h } from '../../app/types/api'

/** Fixtures só aqui: produção desenha apenas o que a API devolve. */
function point(symbol: string, horizon: number, close: number, logReturn = 0.01, fallback = false): ForecastPoint {
  return {
    symbol,
    model_version: '20260824-abc-drift',
    run_at: '2026-08-24T14:33:58Z',
    target_time: `2026-08-${24 + horizon}T00:00:00Z`,
    horizon_days: horizon,
    predicted_close: close,
    predicted_log_return: logReturn,
    pred_lower: close * 0.95,
    pred_upper: close * 1.05,
    is_fallback: fallback,
  }
}

function ticker(symbol: string, lastPrice: number | null): Ticker24h {
  return { symbol, last_price: lastPrice } as Ticker24h
}

function metricsFixture(version: string): ForecastMetrics {
  return {
    model_version: version,
    model_type: 'drift',
    trained_at: '2026-08-24T14:33:58Z',
    is_fallback: false,
    git_sha: 'abc',
    gate: { passed: true, reason: 'ok' },
    skill_score_h1: 0.002,
    per_fold_skill_h1: [0.001],
    per_horizon: { y_1: { mae_log_return: 0.025, rmse_log_return: 0.045, dir_acc: 0.51, n: 2114 } },
    baseline_mae_log_return: { y_1: 0.0254 },
    per_symbol: {
      BTCUSDT: { mae_log_return: 0.014, dir_acc: 0.49, n: 173, confidence: 49 },
      ETHUSDT: { mae_log_return: 0.019, dir_acc: null, n: 38, confidence: null },
    },
    realized_metrics: null,
  }
}

const POINTS = [
  point('BTCUSDT', 1, 101),
  point('BTCUSDT', 7, 107),
  point('ETHUSDT', 1, 49),
  point('ETHUSDT', 7, 51),
]

describe('mapScenarioRows', () => {
  it('diário = 1 dia, semanal = 7 dias; mensal e anual ficam vazios', () => {
    const rows = mapScenarioRows(POINTS, [ticker('BTCUSDT', 100), ticker('ETHUSDT', 50)])
    expect(rows).toHaveLength(2)
    const btc = rows.find(r => r.symbol === 'BTCUSDT')!
    expect(btc.realPrice).toBe(100)
    expect(btc.daily.price).toBe(101)
    expect(btc.daily.changePercent).toBeCloseTo(1)
    expect(btc.weekly.price).toBe(107)
    expect(btc.weekly.changePercent).toBeCloseTo(7)
    expect(btc.monthly).toEqual({ price: null, changePercent: null })
    expect(btc.yearly).toEqual({ price: null, changePercent: null })
    expect(btc.confidence).toBeNull()
  })

  it('variação negativa quando a previsão fica abaixo do preço atual', () => {
    const rows = mapScenarioRows(POINTS, [ticker('ETHUSDT', 50)])
    const eth = rows.find(r => r.symbol === 'ETHUSDT')!
    expect(eth.daily.changePercent).toBeCloseTo(-2)
  })

  it('sem ticker usa o retorno previsto pelo modelo, nunca inventa preço real', () => {
    const rows = mapScenarioRows([point('SOLUSDT', 1, 20, Math.log(1.05))], [])
    const sol = rows[0]!
    expect(sol.realPrice).toBeNull()
    expect(sol.daily.price).toBe(20)
    expect(sol.daily.changePercent).toBeCloseTo(5)
  })

  it('horizonte ausente vira célula vazia', () => {
    const rows = mapScenarioRows([point('BTCUSDT', 1, 101)], [ticker('BTCUSDT', 100)])
    expect(rows[0]!.weekly).toEqual({ price: null, changePercent: null })
  })

  it('sem previsões devolve lista vazia', () => {
    expect(mapScenarioRows([], [ticker('BTCUSDT', 100)])).toEqual([])
  })
})

describe('buildRound', () => {
  const tickers = [ticker('BTCUSDT', 100), ticker('ETHUSDT', 50)]

  it('null sem previsões', () => {
    expect(buildRound([], [])).toBeNull()
  })

  it('média por horizonte, versão e status EM VALIDAÇÃO', () => {
    const rows = mapScenarioRows(POINTS, tickers)
    const round = buildRound(POINTS, rows)!
    expect(round.version).toBe('20260824-abc-drift')
    expect(round.status).toBe('EM VALIDAÇÃO')
    expect(round.generatedAt).toBe('2026-08-24T14:33:58Z')
    const byKey = Object.fromEntries(round.horizons.map(h => [h.key, h.changePercent]))
    expect(byKey.daily).toBeCloseTo((1 + -2) / 2)
    expect(byKey.weekly).toBeCloseTo((7 + 2) / 2)
    expect(byKey.monthly).toBeNull()
    expect(byKey.yearly).toBeNull()
  })

  it('sem métricas, MAE e direção ficam nulos e o modelo cai no rótulo genérico', () => {
    const round = buildRound(POINTS, mapScenarioRows(POINTS, tickers))!
    expect(round.maePercent).toBeNull()
    expect(round.directionAccuracy).toBeNull()
    expect(round.model).toBe('Global')
  })

  it('com métricas da mesma versão, MAE vira % do log-retorno em 1 dia e direção 0–100', () => {
    const metrics = metricsFixture('20260824-abc-drift')
    const rows = mapScenarioRows(POINTS, tickers, metrics)
    const round = buildRound(POINTS, rows, metrics)!
    expect(round.model).toBe('drift')
    expect(round.maePercent).toBeCloseTo(2.5)
    expect(round.directionAccuracy).toBeCloseTo(51)
    expect(rows.find(r => r.symbol === 'BTCUSDT')!.confidence).toBe(49)
    expect(rows.find(r => r.symbol === 'ETHUSDT')!.confidence).toBeNull()
  })

  it('métricas de outra versão são ignoradas — nunca misturar rodadas', () => {
    const metrics = metricsFixture('20260823-zzz-gbm')
    const rows = mapScenarioRows(POINTS, tickers, metrics)
    const round = buildRound(POINTS, rows, metrics)!
    expect(round.maePercent).toBeNull()
    expect(rows[0]!.confidence).toBeNull()
  })

  it('qualquer ponto em fallback marca a rodada como FALLBACK NAIVE', () => {
    const points = [point('BTCUSDT', 1, 101, 0.01, true)]
    const round = buildRound(points, mapScenarioRows(points, tickers))!
    expect(round.status).toBe('FALLBACK NAIVE')
    expect(round.narrative).toContain('fallback')
  })
})

describe('buildNarrative', () => {
  it('primeira frase curta vira manchete e cita contagem e médias reais', () => {
    const text = buildNarrative(16, '2026-08-24T14:33:58Z', 0.42, -1.3, false)
    expect(text.startsWith('16 ativos projetados de 1 a 7 dias.')).toBe(true)
    expect(text).toContain('+0,4 %')
    expect(text).toContain('−1,3 %')
  })

  it('sem médias explica a ausência em vez de inventar', () => {
    expect(buildNarrative(3, '2026-08-24T14:33:58Z', null, null, false)).toContain('sem base de preço atual')
  })
})

describe('gapTop', () => {
  it('ordena por magnitude e ignora ativo sem preço atual', () => {
    const rows = mapScenarioRows(
      [point('AAAUSDT', 1, 103), point('BBBUSDT', 1, 95), point('CCCUSDT', 1, 101), point('DDDUSDT', 1, 120)],
      [ticker('AAAUSDT', 100), ticker('BBBUSDT', 100), ticker('CCCUSDT', 100)],
    )
    const gap = gapTop(rows)
    expect(gap.map(r => r.symbol)).toEqual(['BBBUSDT', 'AAAUSDT', 'CCCUSDT'])
    expect(gap[0]!.value).toBeCloseTo(-5)
    expect(gap[0]!.delta).toBeNull()
  })

  it('respeita o limite', () => {
    const rows = mapScenarioRows(
      Array.from({ length: 8 }, (_, i) => point(`S${i}USDT`, 1, 100 + i + 1)),
      Array.from({ length: 8 }, (_, i) => ticker(`S${i}USDT`, 100)),
    )
    expect(gapTop(rows, 5)).toHaveLength(5)
  })
})

describe('mapMonteCarlo', () => {
  const out: MonteCarloSeriesOut = {
    symbol: 'BTCUSDT',
    horizonDays: 7,
    observed: [{ time: 200, value: 101 }, { time: 100, value: 100 }],
    stepSeconds: 86_400,
    paths: [[102, 104], [99, 97]],
    simulatedCount: 1000,
    classified: { best: 0, worst: 1, base: null },
  }

  it('ordena o observado e normaliza classified (null vira ausente)', () => {
    const series = mapMonteCarlo(out)
    expect(series.observed.map(p => p.time)).toEqual([100, 200])
    expect(series.classified).toEqual({ best: 0, worst: 1, base: undefined })
    expect(series.paths).toBe(out.paths)
    expect(series.simulatedCount).toBe(1000)
  })

  it('sem classified da API, deixa a seleção para o front', () => {
    expect(mapMonteCarlo({ ...out, classified: null }).classified).toBeUndefined()
  })
})
