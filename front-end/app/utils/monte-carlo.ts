import type { MonteCarloSeries } from '~/types/forecast'

/**
 * Seleção e estatística do Monte Carlo (Design.md §11.3).
 *
 * Tudo aqui é **seleção visual sobre trajetórias já recebidas** — nenhuma função
 * cria, extrapola ou simula valores. Puras e testáveis em Node.
 */

export interface HighlightedPaths {
  best: number
  base: number
  worst: number
}

/** Último valor de uma trajetória; `null` se ela vier vazia. */
export function terminalValue(path: readonly number[]): number | null {
  return path.length ? (path[path.length - 1] as number) : null
}

/**
 * Índices de melhor, base e pior caminho.
 *
 * Se a API classificou, essa classificação vence. Caso contrário, escolhe entre
 * as trajetórias reais recebidas: maior valor terminal, menor valor terminal e a
 * mais próxima da mediana terminal.
 */
export function selectHighlighted(
  paths: readonly (readonly number[])[],
  classified?: MonteCarloSeries['classified'],
): HighlightedPaths | null {
  const valid = paths
    .map((path, index) => ({ index, terminal: terminalValue(path) }))
    .filter((p): p is { index: number, terminal: number } => p.terminal !== null && Number.isFinite(p.terminal))
  if (!valid.length) return null

  const inRange = (i: number | undefined): i is number => i !== undefined && i >= 0 && i < paths.length && (paths[i]?.length ?? 0) > 0

  const sorted = [...valid].sort((a, b) => a.terminal - b.terminal)
  const lowest = sorted[0] as { index: number, terminal: number }
  const highest = sorted[sorted.length - 1] as { index: number, terminal: number }
  const medianTerminal = median(sorted.map(p => p.terminal))
  const nearestMedian = sorted.reduce((acc, p) =>
    Math.abs(p.terminal - medianTerminal) < Math.abs(acc.terminal - medianTerminal) ? p : acc, lowest)

  return {
    best: inRange(classified?.best) ? classified.best : highest.index,
    worst: inRange(classified?.worst) ? classified.worst : lowest.index,
    base: inRange(classified?.base) ? classified.base : nearestMedian.index,
  }
}

/**
 * Remove trajetórias vazias preservando a classificação da API: os índices de
 * `classified` apontam para o array original e são remapeados para o filtrado —
 * sem isso, o melhor caminho pode virar o pior depois do filtro. Índices que
 * apontavam para uma trajetória removida caem no fallback de `selectHighlighted`.
 */
export function filterPaths(
  paths: readonly (readonly number[])[],
  classified?: MonteCarloSeries['classified'],
): { paths: (readonly number[])[], classified?: MonteCarloSeries['classified'] } {
  const entries = paths
    .map((path, index) => ({ index, path }))
    .filter(e => e.path.length > 0)
  const filteredIndex = new Map(entries.map((e, i) => [e.index, i]))
  const remap = (i?: number) => (i === undefined ? undefined : filteredIndex.get(i))
  return {
    paths: entries.map(e => e.path),
    classified: classified
      ? { best: remap(classified.best), base: remap(classified.base), worst: remap(classified.worst) }
      : undefined,
  }
}

export function median(sortedAscending: readonly number[]): number {
  const n = sortedAscending.length
  if (!n) return Number.NaN
  const mid = Math.floor(n / 2)
  if (n % 2) return sortedAscending[mid] as number
  return (((sortedAscending[mid - 1] as number) + (sortedAscending[mid] as number)) / 2)
}

export interface UncertaintyBand {
  low: number[]
  high: number[]
}

/**
 * Faixa de incerteza por passo (quantis das trajetórias reais). Nasce estreita
 * na linha de corte porque todos os caminhos partem do mesmo ponto observado, e
 * abre com o horizonte — é uma consequência dos dados, não um efeito desenhado.
 */
export function quantileBand(
  paths: readonly (readonly number[])[],
  lowQuantile = 0.1,
  highQuantile = 0.9,
): UncertaintyBand {
  const steps = paths.reduce((max, p) => Math.max(max, p.length), 0)
  const low: number[] = []
  const high: number[] = []
  for (let step = 0; step < steps; step++) {
    const column: number[] = []
    for (const path of paths) {
      const v = path[step]
      if (typeof v === 'number' && Number.isFinite(v)) column.push(v)
    }
    if (!column.length) {
      low.push(Number.NaN)
      high.push(Number.NaN)
      continue
    }
    column.sort((a, b) => a - b)
    low.push(quantile(column, lowQuantile))
    high.push(quantile(column, highQuantile))
  }
  return { low, high }
}

/** Quantil por interpolação linear sobre um array já ordenado. */
export function quantile(sortedAscending: readonly number[], q: number): number {
  const n = sortedAscending.length
  if (!n) return Number.NaN
  const pos = Math.min(n - 1, Math.max(0, (n - 1) * q))
  const lower = Math.floor(pos)
  const upper = Math.ceil(pos)
  const a = sortedAscending[lower] as number
  if (lower === upper) return a
  const b = sortedAscending[upper] as number
  return a + (b - a) * (pos - lower)
}

/**
 * Amostra visual determinística: preserva a ordem e sempre mantém os índices
 * destacados. Desenhar 1.000 caminhos é possível em canvas, mas a amostragem
 * mantém a taxa de quadros em telas pequenas — a UI informa a quantidade real.
 */
export function sampleIndices(total: number, max: number, keep: readonly number[] = []): number[] {
  if (total <= max) return Array.from({ length: total }, (_, i) => i)
  const stride = total / max
  const picked = new Set<number>(keep.filter(i => i >= 0 && i < total))
  for (let i = 0; i < max; i++) picked.add(Math.min(total - 1, Math.floor(i * stride)))
  return [...picked].sort((a, b) => a - b)
}

/** Faixa [min, max] de todos os valores visíveis, com folga relativa. */
export function valueExtent(values: readonly number[], padding = 0.06): { min: number, max: number } | null {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  for (const v of values) {
    if (!Number.isFinite(v)) continue
    if (v < min) min = v
    if (v > max) max = v
  }
  if (min === Number.POSITIVE_INFINITY) return null
  if (min === max) {
    const delta = Math.abs(min) * 0.02 || 1
    return { min: min - delta, max: max + delta }
  }
  const span = max - min
  return { min: min - span * padding, max: max + span * padding }
}
