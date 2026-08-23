import type { CandlestickData, HistogramData, LineData, UTCTimestamp, WhitespaceData } from 'lightweight-charts'
import type { FeatureKey, FeatureRow, Kline } from '~/types/api'

export type LinePoint = LineData<UTCTimestamp> | WhitespaceData<UTCTimestamp>

/**
 * Cenários do modelo (Design.md §2.4): três trajetórias depois da linha de corte.
 * Cada série começa na última vela real — nunca inventadas no front (marco 3).
 */
export interface ScenarioSet {
  best: LinePoint[]
  expected: LinePoint[]
  worst: LinePoint[]
}

/** ISO 8601 → segundos UTC (Lightweight Charts usa segundos, não ms). */
export function toUtcSeconds(iso: string): UTCTimestamp {
  return Math.floor(Date.parse(iso) / 1000) as UTCTimestamp
}

/** Ordena ascendente por tempo e remove duplicatas (mantém a última ocorrência). */
export function sortAscendingUnique<T extends { time: UTCTimestamp }>(points: T[]): T[] {
  const byTime = new Map<number, T>()
  for (const p of points) byTime.set(p.time, p)
  return [...byTime.values()].sort((a, b) => a.time - b.time)
}

/** A API devolve newest-first; o gráfico exige ascendente e único. */
export function klinesToCandles(rows: readonly Kline[]): CandlestickData<UTCTimestamp>[] {
  return sortAscendingUnique(rows.map(r => ({
    time: toUtcSeconds(r.open_time),
    open: r.open,
    high: r.high,
    low: r.low,
    close: r.close,
  })))
}

export interface VolumeColors { up: string, down: string }

export function klinesToVolume(rows: readonly Kline[], colors: VolumeColors): HistogramData<UTCTimestamp>[] {
  return sortAscendingUnique(rows.map(r => ({
    time: toUtcSeconds(r.open_time),
    value: r.volume,
    color: r.close >= r.open ? colors.up : colors.down,
  })))
}

/** Um campo de features → linha; `null` (warm-up) vira WhitespaceData (gap), nunca zero. */
export function featureToLine(rows: readonly FeatureRow[], key: FeatureKey): LinePoint[] {
  return sortAscendingUnique(rows.map((r) => {
    const time = toUtcSeconds(r.timestamp)
    const value = r[key]
    return value === null || value === undefined ? { time } : { time, value }
  }))
}

export interface HistogramColors { positive: string, negative: string }

export function featureToHistogram(rows: readonly FeatureRow[], key: FeatureKey, colors: HistogramColors): (HistogramData<UTCTimestamp> | WhitespaceData<UTCTimestamp>)[] {
  return sortAscendingUnique(rows.map((r) => {
    const time = toUtcSeconds(r.timestamp)
    const value = r[key]
    if (value === null || value === undefined) return { time }
    return { time, value, color: value >= 0 ? colors.positive : colors.negative }
  }))
}

export interface WarmupInfo {
  /** Primeiro timestamp (ISO) com valor não nulo, se houver. */
  firstValueAt: string | null
  /** Quantas linhas ainda faltam para o primeiro valor (quando nenhum valor existe). */
  missing: number | null
  hasAnyValue: boolean
}

/**
 * Warm-up de um indicador numa janela: onde a linha começa e, se ainda não começou,
 * quantas velas faltam dado o período de cálculo.
 */
export function warmupInfo(rows: readonly FeatureRow[], key: FeatureKey, window?: number): WarmupInfo {
  const ascending = [...rows].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp))
  const first = ascending.find(r => r[key] !== null && r[key] !== undefined)
  if (first) return { firstValueAt: first.timestamp, missing: null, hasAnyValue: true }
  const missing = window !== undefined ? Math.max(0, window - ascending.length) : null
  return { firstValueAt: null, missing, hasAnyValue: false }
}

/** Último valor não nulo de uma chave (para legenda sem crosshair). */
export function lastValue(rows: readonly FeatureRow[], key: FeatureKey): number | null {
  // rows são newest-first na API, mas não dependemos disso
  let best: { t: number, v: number } | null = null
  for (const r of rows) {
    const v = r[key]
    if (v === null || v === undefined) continue
    const t = Date.parse(r.timestamp)
    if (!best || t > best.t) best = { t, v }
  }
  return best?.v ?? null
}

/** Valor de uma chave num timestamp exato (segundos UTC); null se ausente/warm-up. */
export function valueAt(rows: readonly FeatureRow[], key: FeatureKey, time: UTCTimestamp): number | null {
  for (const r of rows) {
    if (toUtcSeconds(r.timestamp) === time) {
      const v = r[key]
      return v === null || v === undefined ? null : v
    }
  }
  return null
}

/** Data da última vela (ISO) — para o selo de snapshot. */
export function latestOpenTime(rows: readonly Kline[]): string | null {
  let best: string | null = null
  let bestT = -Infinity
  for (const r of rows) {
    const t = Date.parse(r.open_time)
    if (t > bestT) {
      bestT = t
      best = r.open_time
    }
  }
  return best
}
