<script setup lang="ts">
import { useDocumentVisibility, useResizeObserver } from '@vueuse/core'
import type { MonteCarloSeries } from '~/types/forecast'
import { MONTE_CARLO_COLORS } from '~/utils/constants'
import { filterPaths, quantileBand, sampleIndices, selectHighlighted, valueExtent } from '~/utils/monte-carlo'
import { formatNumber, formatPercent, formatUtcShort } from '~/utils/format'
import { easeSection } from '~/utils/motion'

/**
 * Simulação Monte Carlo (Design.md §11.3) — visualização full-bleed, sem container
 * emoldurado.
 *
 * Regra dura: este componente **nunca gera valores financeiros**. Ele desenha as
 * trajetórias reais que chegam por `series.paths`, escolhe visualmente três delas
 * (melhor/base/pior) e calcula a faixa de incerteza como quantis dessas mesmas
 * trajetórias. Sem `series`, mostra o estado vazio honesto.
 *
 * Canvas 2D: 1.000 trajetórias em SVG seriam 1.000 nós no DOM.
 */
const props = defineProps<{
  series: MonteCarloSeries | null
  /** Incrementar reinicia o desenho progressivo com as mesmas trajetórias. */
  restartToken?: number
}>()

/** Duração total do desenho progressivo: dentro de 1,6–2,2 s. */
const DRAW_MS = 1900
/** Fração da duração usada para escalonar as ondas de trajetórias. */
const WAVE_SPREAD = 0.4
const WAVES = 6
/** Teto de trajetórias desenhadas; a UI informa a quantidade real simulada. */
const MAX_DRAWN = 320

const reduced = useReducedMotion()
const visibility = useDocumentVisibility()

const host = ref<HTMLDivElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
const inView = useEnterOnce(host, 0.2)

// ---------- Preparo dos dados (puro, sem geração) ----------

/**
 * Toda trajetória é ancorada no último dado observado: o cenário começa
 * exatamente na linha de corte (Design.md §10). O ponto âncora é o valor real
 * observado, não uma previsão.
 */
const prepared = computed(() => {
  const s = props.series
  if (!s || !s.observed.length || !s.paths.length) return null

  const observed = [...s.observed].sort((a, b) => a.time - b.time)
  const anchor = observed[observed.length - 1]
  if (!anchor) return null

  const filtered = filterPaths(s.paths, s.classified)
  if (!filtered.paths.length) return null

  const paths = filtered.paths.map(p => [anchor.value, ...p])
  const steps = paths.reduce((max, p) => Math.max(max, p.length), 0)
  const highlighted = selectHighlighted(filtered.paths, filtered.classified)
  const band = quantileBand(paths)

  const cutIndex = observed.length - 1
  const maxIndex = cutIndex + steps - 1

  const drawn = sampleIndices(paths.length, MAX_DRAWN, highlighted ? [highlighted.best, highlighted.base, highlighted.worst] : [])

  return { observed, anchor, paths, steps, highlighted, band, cutIndex, maxIndex, drawn, simulatedCount: s.simulatedCount, stepSeconds: s.stepSeconds }
})

/** Rótulos finais dos três caminhos destacados (só depois do desenho terminar). */
const highlightSummary = computed(() => {
  const p = prepared.value
  if (!p || !p.highlighted) return null
  const base = p.anchor.value
  const of = (index: number) => {
    const path = p.paths[index]
    const terminal = path?.[path.length - 1]
    if (terminal === undefined) return null
    return { value: terminal, change: base === 0 ? null : ((terminal - base) / base) * 100 }
  }
  return {
    best: of(p.highlighted.best),
    base: of(p.highlighted.base),
    worst: of(p.highlighted.worst),
  }
})

// ---------- Janela visível (pan / zoom em espaço lógico) ----------
const viewFrom = ref(0)
const viewTo = ref(1)

function resetView() {
  const p = prepared.value
  viewFrom.value = 0
  viewTo.value = p ? p.maxIndex : 1
}

function clampView(from: number, to: number) {
  const p = prepared.value
  if (!p) return
  const minSpan = 6
  const maxSpan = p.maxIndex
  let span = Math.min(maxSpan, Math.max(minSpan, to - from))
  if (!Number.isFinite(span) || span <= 0) span = maxSpan
  let start = Math.min(Math.max(0, from), Math.max(0, p.maxIndex - span))
  if (start < 0) start = 0
  viewFrom.value = start
  viewTo.value = start + span
}

function panByFraction(fraction: number) {
  const span = viewTo.value - viewFrom.value
  clampView(viewFrom.value + span * fraction, viewTo.value + span * fraction)
  scheduleRender()
}

function zoomAround(anchorIndex: number, factor: number) {
  const from = anchorIndex - (anchorIndex - viewFrom.value) * factor
  const to = anchorIndex + (viewTo.value - anchorIndex) * factor
  clampView(from, to)
  scheduleRender()
}

// ---------- Geometria ----------
/**
 * A margem direita abre em telas largas para receber os rótulos MELHOR/BASE/PIOR
 * ancorados no fim de cada trajetória (mockup 06). Abaixo de 760 px os rótulos
 * saem e a legenda embaixo do gráfico assume o papel.
 */
const PAD = reactive({ top: 22, right: 176, bottom: 34, left: 62 })
const showTerminalLabels = ref(true)

interface Layout { width: number, height: number, plotW: number, plotH: number, min: number, max: number }
let layout: Layout | null = null

function computeLayout(width: number, height: number): Layout | null {
  const p = prepared.value
  if (!p) return null
  showTerminalLabels.value = width >= 760
  PAD.right = showTerminalLabels.value ? 176 : 52
  PAD.left = width >= 760 ? 62 : 52
  const plotW = Math.max(10, width - PAD.left - PAD.right)
  const plotH = Math.max(10, height - PAD.top - PAD.bottom)

  const values: number[] = []
  const from = Math.floor(viewFrom.value)
  const to = Math.ceil(viewTo.value)
  for (let i = Math.max(0, from); i <= Math.min(p.cutIndex, to); i++) {
    const point = p.observed[i]
    if (point) values.push(point.value)
  }
  for (let step = 0; step < p.steps; step++) {
    const index = p.cutIndex + step
    if (index < from || index > to) continue
    const lo = p.band.low[step]
    const hi = p.band.high[step]
    if (Number.isFinite(lo)) values.push(lo as number)
    if (Number.isFinite(hi)) values.push(hi as number)
  }
  if (p.highlighted) {
    for (const index of [p.highlighted.best, p.highlighted.base, p.highlighted.worst]) {
      const path = p.paths[index]
      if (!path) continue
      for (let step = 0; step < path.length; step++) {
        const idx = p.cutIndex + step
        if (idx < from || idx > to) continue
        const v = path[step]
        if (typeof v === 'number') values.push(v)
      }
    }
  }
  const extent = valueExtent(values)
  if (!extent) return null
  return { width, height, plotW, plotH, min: extent.min, max: extent.max }
}

function xOf(index: number, l: Layout): number {
  const span = viewTo.value - viewFrom.value || 1
  return PAD.left + ((index - viewFrom.value) / span) * l.plotW
}

function yOf(value: number, l: Layout): number {
  const span = l.max - l.min || 1
  return PAD.top + (1 - (value - l.min) / span) * l.plotH
}

/** Segundos UTC de um índice lógico (observado ou passo previsto). */
function timeAt(index: number): number | null {
  const p = prepared.value
  if (!p) return null
  if (index <= p.cutIndex) return p.observed[Math.max(0, Math.round(index))]?.time ?? null
  const anchorTime = p.observed[p.cutIndex]?.time
  if (anchorTime === undefined) return null
  return anchorTime + Math.round(index - p.cutIndex) * p.stepSeconds
}

// ---------- Desenho ----------
const progress = ref(0)
const crosshairIndex = ref<number | null>(null)

function cssVar(name: string, fallback: string): string {
  if (!host.value) return fallback
  return getComputedStyle(host.value).getPropertyValue(name).trim() || fallback
}

function render() {
  const canvas = canvasEl.value
  const p = prepared.value
  if (!canvas || !p) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = Math.min(2, globalThis.devicePixelRatio || 1)
  const width = canvas.clientWidth
  const height = canvas.clientHeight
  if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
    canvas.width = Math.round(width * dpr)
    canvas.height = Math.round(height * dpr)
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, width, height)

  const l = computeLayout(width, height)
  if (!l) return
  layout = l

  const hairline = cssVar('--cf-hairline-soft', 'rgba(216,231,245,.07)')
  const dim = cssVar('--cf-text-dim', '#66788f')
  const t = progress.value

  drawGrid(ctx, l, hairline, dim)
  drawBand(ctx, l, p, t)
  drawSecondaryPaths(ctx, l, p, t)
  drawObserved(ctx, l, p)
  drawCutLine(ctx, l, p)
  drawHighlights(ctx, l, p, t)
  drawCrosshair(ctx, l, dim)
  updateLabelAnchors(l, p)
}

interface LabelAnchor { key: 'best' | 'base' | 'worst', x: number, y: number }
const labelAnchors = ref<LabelAnchor[]>([])

/**
 * Posição vertical de cada rótulo = fim visível da sua trajetória. Recalculado a
 * cada quadro para acompanhar pan e zoom; só aparece com o desenho concluído.
 */
function updateLabelAnchors(l: Layout, p: Prepared) {
  if (progress.value < 1 || !p.highlighted || !showTerminalLabels.value) {
    if (labelAnchors.value.length) labelAnchors.value = []
    return
  }
  const x = PAD.left + l.plotW + 12
  const entries: LabelAnchor[] = []
  for (const [key, index] of [['best', p.highlighted.best], ['base', p.highlighted.base], ['worst', p.highlighted.worst]] as const) {
    const path = p.paths[index]
    if (!path) continue
    const step = Math.max(0, Math.min(path.length - 1, Math.floor(viewTo.value - p.cutIndex)))
    const value = path[step]
    if (typeof value !== 'number') continue
    entries.push({ key, x, y: Math.round(Math.min(PAD.top + l.plotH - 6, Math.max(PAD.top + 6, yOf(value, l)))) })
  }
  labelAnchors.value = entries
}

type Prepared = NonNullable<typeof prepared.value>

function drawGrid(ctx: CanvasRenderingContext2D, l: Layout, hairline: string, dim: string) {
  ctx.save()
  ctx.strokeStyle = hairline
  ctx.lineWidth = 1
  ctx.fillStyle = dim
  ctx.font = '11px "Geist Mono", ui-monospace, monospace'
  ctx.textBaseline = 'middle'

  const TICKS = 5
  for (let i = 0; i <= TICKS; i++) {
    const value = l.min + ((l.max - l.min) * i) / TICKS
    const y = Math.round(yOf(value, l)) + 0.5
    ctx.beginPath()
    ctx.moveTo(PAD.left, y)
    ctx.lineTo(PAD.left + l.plotW, y)
    ctx.stroke()
    ctx.textAlign = 'right'
    ctx.fillText(formatNumber(value, value >= 1000 ? 0 : 2), PAD.left - 10, y)
  }

  // Eixo de tempo: rótulos em UTC, espaçados pela largura disponível.
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  const span = viewTo.value - viewFrom.value
  const labelCount = Math.max(2, Math.min(8, Math.floor(l.plotW / 110)))
  for (let i = 0; i <= labelCount; i++) {
    const index = viewFrom.value + (span * i) / labelCount
    const time = timeAt(index)
    if (time === null) continue
    ctx.fillText(formatUtcShort(time * 1000, { withTime: false }).toUpperCase(), xOf(index, l), PAD.top + l.plotH + 12)
  }
  ctx.restore()
}

function drawBand(ctx: CanvasRenderingContext2D, l: Layout, p: Prepared, t: number) {
  if (t <= 0) return
  ctx.save()
  ctx.fillStyle = MONTE_CARLO_COLORS.band
  ctx.globalAlpha = Math.min(1, t * 1.4)
  ctx.beginPath()
  let started = false
  for (let step = 0; step < p.steps; step++) {
    const v = p.band.high[step]
    if (!Number.isFinite(v)) continue
    const x = xOf(p.cutIndex + step, l)
    const y = yOf(v as number, l)
    if (started) ctx.lineTo(x, y)
    else {
      ctx.moveTo(x, y)
      started = true
    }
  }
  for (let step = p.steps - 1; step >= 0; step--) {
    const v = p.band.low[step]
    if (!Number.isFinite(v)) continue
    ctx.lineTo(xOf(p.cutIndex + step, l), yOf(v as number, l))
  }
  if (started) {
    ctx.closePath()
    ctx.fill()
  }
  ctx.restore()
}

/** Fração desenhada de uma trajetória, dado o tempo normalizado e sua onda. */
function waveProgress(t: number, waveIndex: number): number {
  const delay = (waveIndex / WAVES) * WAVE_SPREAD
  return Math.min(1, Math.max(0, (t - delay) / (1 - WAVE_SPREAD)))
}

function strokePath(ctx: CanvasRenderingContext2D, l: Layout, p: Prepared, path: readonly number[], fraction: number) {
  const last = Math.min(path.length - 1, Math.floor(fraction * (path.length - 1)))
  if (last < 1) return
  ctx.beginPath()
  for (let step = 0; step <= last; step++) {
    const v = path[step]
    if (typeof v !== 'number' || !Number.isFinite(v)) continue
    const x = xOf(p.cutIndex + step, l)
    const y = yOf(v, l)
    if (step === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()
}

function drawSecondaryPaths(ctx: CanvasRenderingContext2D, l: Layout, p: Prepared, t: number) {
  if (t <= 0) return
  const skip = p.highlighted ? new Set([p.highlighted.best, p.highlighted.base, p.highlighted.worst]) : new Set<number>()
  ctx.save()
  ctx.strokeStyle = MONTE_CARLO_COLORS.path
  ctx.lineWidth = 1
  ctx.lineJoin = 'round'
  let wave = 0
  for (const index of p.drawn) {
    wave = (wave + 1) % WAVES
    if (skip.has(index)) continue
    const path = p.paths[index]
    if (!path) continue
    strokePath(ctx, l, p, path, waveProgress(t, wave))
  }
  ctx.restore()
}

function drawObserved(ctx: CanvasRenderingContext2D, l: Layout, p: Prepared) {
  ctx.save()
  ctx.strokeStyle = MONTE_CARLO_COLORS.observed
  ctx.lineWidth = 1.4
  ctx.lineJoin = 'round'
  ctx.beginPath()
  let started = false
  for (let i = 0; i <= p.cutIndex; i++) {
    const point = p.observed[i]
    if (!point) continue
    const x = xOf(i, l)
    const y = yOf(point.value, l)
    if (started) ctx.lineTo(x, y)
    else {
      ctx.moveTo(x, y)
      started = true
    }
  }
  ctx.stroke()
  ctx.restore()
}

function drawCutLine(ctx: CanvasRenderingContext2D, l: Layout, p: Prepared) {
  const x = Math.round(xOf(p.cutIndex, l)) + 0.5
  ctx.save()
  ctx.strokeStyle = MONTE_CARLO_COLORS.cut
  ctx.globalAlpha = 0.85
  ctx.setLineDash([3, 4])
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(x, PAD.top)
  ctx.lineTo(x, PAD.top + l.plotH)
  ctx.stroke()
  ctx.setLineDash([])
  ctx.globalAlpha = 1
  ctx.fillStyle = MONTE_CARLO_COLORS.cut
  ctx.beginPath()
  ctx.arc(x, yOf(p.anchor.value, l), 3.5, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()
}

function drawHighlights(ctx: CanvasRenderingContext2D, l: Layout, p: Prepared, t: number) {
  if (!p.highlighted) return
  // Destaque cresce suavemente na reta final; rótulos só depois de terminar.
  const emphasis = Math.min(1, Math.max(0, (t - 0.7) / 0.3))
  const defs = [
    { index: p.highlighted.worst, color: MONTE_CARLO_COLORS.worst, wave: 1 },
    { index: p.highlighted.base, color: MONTE_CARLO_COLORS.base, wave: 0 },
    { index: p.highlighted.best, color: MONTE_CARLO_COLORS.best, wave: 2 },
  ]
  ctx.save()
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  for (const def of defs) {
    const path = p.paths[def.index]
    if (!path) continue
    ctx.strokeStyle = def.color
    ctx.globalAlpha = 0.55 + 0.45 * emphasis
    ctx.lineWidth = 1.4 + 1.0 * emphasis
    strokePath(ctx, l, p, path, waveProgress(t, def.wave))
  }
  ctx.restore()
}

function drawCrosshair(ctx: CanvasRenderingContext2D, l: Layout, dim: string) {
  const index = crosshairIndex.value
  if (index === null) return
  const x = Math.round(xOf(index, l)) + 0.5
  if (x < PAD.left || x > PAD.left + l.plotW) return
  ctx.save()
  ctx.strokeStyle = dim
  ctx.setLineDash([2, 3])
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(x, PAD.top)
  ctx.lineTo(x, PAD.top + l.plotH)
  ctx.stroke()
  ctx.restore()
}

// ---------- Loop de animação ----------
let frame: number | null = null
let renderFrame: number | null = null
let startedAt = 0
let elapsedBeforePause = 0
let animating = false

function cancelFrames() {
  if (frame !== null) cancelAnimationFrame(frame)
  if (renderFrame !== null) cancelAnimationFrame(renderFrame)
  frame = null
  renderFrame = null
}

function scheduleRender() {
  if (animating || renderFrame !== null) return
  renderFrame = requestAnimationFrame(() => {
    renderFrame = null
    render()
  })
}

function step(now: number) {
  const total = elapsedBeforePause + (now - startedAt)
  progress.value = Math.min(1, easeSection(total / DRAW_MS))
  render()
  if (progress.value >= 1) {
    animating = false
    frame = null
    return
  }
  frame = requestAnimationFrame(step)
}

/** Reinicia o desenho: sempre cancela o quadro anterior antes de agendar outro. */
function startAnimation() {
  cancelFrames()
  if (!prepared.value) return
  if (reduced.value) {
    // Redução de movimento: tudo completo, sem desenho progressivo.
    animating = false
    progress.value = 1
    render()
    return
  }
  progress.value = 0
  elapsedBeforePause = 0
  animating = true
  startedAt = performance.now()
  frame = requestAnimationFrame(step)
}

function pauseAnimation() {
  if (!animating || frame === null) return
  cancelAnimationFrame(frame)
  frame = null
  elapsedBeforePause += performance.now() - startedAt
}

function resumeAnimation() {
  if (!animating || frame !== null) return
  startedAt = performance.now()
  frame = requestAnimationFrame(step)
}

watch(visibility, (state) => {
  // Nenhum trabalho de animação com a aba oculta.
  if (state === 'hidden') pauseAnimation()
  else resumeAnimation()
})

// ---------- Interação por ponteiro ----------
let dragging = false
let dragStartX = 0
let dragStartFrom = 0

function indexFromClientX(clientX: number): number | null {
  const canvas = canvasEl.value
  if (!canvas || !layout) return null
  const rect = canvas.getBoundingClientRect()
  const x = clientX - rect.left
  const span = viewTo.value - viewFrom.value
  return viewFrom.value + ((x - PAD.left) / layout.plotW) * span
}

function onPointerDown(event: PointerEvent) {
  if (!prepared.value) return
  dragging = true
  dragStartX = event.clientX
  dragStartFrom = viewFrom.value
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function onPointerMove(event: PointerEvent) {
  if (!prepared.value || !layout) return
  if (dragging) {
    const span = viewTo.value - viewFrom.value
    const deltaIndex = ((event.clientX - dragStartX) / layout.plotW) * span
    clampView(dragStartFrom - deltaIndex, dragStartFrom - deltaIndex + span)
    scheduleRender()
    return
  }
  const index = indexFromClientX(event.clientX)
  crosshairIndex.value = index === null ? null : Math.round(index)
  scheduleRender()
}

function onPointerUp(event: PointerEvent) {
  dragging = false
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture?.(event.pointerId)) target.releasePointerCapture(event.pointerId)
}

function onPointerLeave() {
  dragging = false
  crosshairIndex.value = null
  scheduleRender()
}

function onWheel(event: WheelEvent) {
  if (!prepared.value) return
  event.preventDefault()
  const index = indexFromClientX(event.clientX)
  if (index === null) return
  zoomAround(index, event.deltaY > 0 ? 1.15 : 1 / 1.15)
}

// ---------- Tooltip ----------
const tooltip = computed(() => {
  const p = prepared.value
  const index = crosshairIndex.value
  if (!p || !p.highlighted || index === null || progress.value < 1) return null
  const step = Math.round(index) - p.cutIndex
  if (step < 0 || step >= p.steps) return null
  const time = timeAt(p.cutIndex + step)
  const read = (pathIndex: number) => {
    const value = p.paths[pathIndex]?.[step]
    if (typeof value !== 'number') return null
    const change = p.anchor.value === 0 ? null : ((value - p.anchor.value) / p.anchor.value) * 100
    return { value, change }
  }
  return {
    time,
    best: read(p.highlighted.best),
    base: read(p.highlighted.base),
    worst: read(p.highlighted.worst),
  }
})

const tooltipStyle = computed(() => {
  const index = crosshairIndex.value
  if (index === null || !layout) return { display: 'none' }
  const x = xOf(index, layout)
  const flip = x > layout.plotW * 0.6
  return {
    left: `${flip ? x - 200 : x + 14}px`,
    top: `${PAD.top + 8}px`,
  }
})

// ---------- Ciclo de vida ----------
// Redimensionar redesenha com a janela lógica atual — sem reiniciar a animação.
useResizeObserver(host, () => scheduleRender())

watch(prepared, () => {
  resetView()
  if (inView.value) startAnimation()
  else render()
})

watch(inView, (visible) => {
  if (visible) startAnimation()
})

watch(() => props.restartToken, () => startAnimation())

watch(reduced, (isReduced) => {
  if (!isReduced) return
  cancelFrames()
  animating = false
  progress.value = 1
  render()
})

onMounted(() => {
  resetView()
  if (inView.value) startAnimation()
  else render()
})

onBeforeUnmount(cancelFrames)

// ---------- Acessibilidade ----------
const ariaLabel = computed(() => {
  const p = prepared.value
  const s = props.series
  if (!p || !s) return 'Simulação Monte Carlo sem dados'
  return `Simulação Monte Carlo de ${s.symbol}, ${formatNumber(p.simulatedCount, 0)} trajetórias simuladas em ${s.horizonDays} dias, a partir do último dado observado em ${formatUtcShort(p.anchor.time * 1000, { withTime: false, withYear: true })} UTC.`
})

const tableOpen = ref(false)
const tableRows = computed(() => {
  const p = prepared.value
  if (!p || !p.highlighted) return []
  const rows: { date: string, best: string, base: string, worst: string }[] = []
  for (let step = 0; step < p.steps; step++) {
    const time = timeAt(p.cutIndex + step)
    const cell = (index: number) => {
      const v = p.paths[index]?.[step]
      return typeof v === 'number' ? formatNumber(v, v >= 1000 ? 0 : 2) : '—'
    }
    rows.push({
      date: time === null ? '—' : formatUtcShort(time * 1000, { withTime: false, withYear: true }),
      best: cell(p.highlighted.best),
      base: cell(p.highlighted.base),
      worst: cell(p.highlighted.worst),
    })
  }
  return rows
})

const NAV_ACTIONS = [
  { key: 'left', icon: 'i-lucide-chevron-left', label: 'Deslocar para trás' },
  { key: 'right', icon: 'i-lucide-chevron-right', label: 'Deslocar para frente' },
  { key: 'out', icon: 'i-lucide-minus', label: 'Afastar' },
  { key: 'in', icon: 'i-lucide-plus', label: 'Aproximar' },
  { key: 'fit', icon: 'i-lucide-maximize-2', label: 'Enquadrar tudo' },
] as const

function runNav(key: (typeof NAV_ACTIONS)[number]['key']) {
  const center = (viewFrom.value + viewTo.value) / 2
  if (key === 'left') panByFraction(-0.2)
  else if (key === 'right') panByFraction(0.2)
  else if (key === 'out') zoomAround(center, 1.25)
  else if (key === 'in') zoomAround(center, 1 / 1.25)
  else {
    resetView()
    scheduleRender()
  }
}

const labelsVisible = computed(() => progress.value >= 1)

defineExpose({ restart: startAnimation })
</script>

<template>
  <div ref="host">
    <!-- Sem trajetórias reais: estado honesto, nada é desenhado (Design.md §13.3) -->
    <div
      v-if="!prepared"
      class="cf-hairline-t max-w-[62ch] pt-8"
      role="status"
    >
      <p class="text-[15px] text-muted">
        O modelo ainda não publicou previsões para este ativo.
      </p>
      <p class="mt-2 text-[13px] text-dimmed">
        Quando a primeira rodada sair, esta área desenha as trajetórias simuladas a
        partir do último dado observado, destacando melhor caso, cenário base e pior caso.
      </p>
    </div>

    <template v-else>
      <div class="relative">
        <canvas
          ref="canvasEl"
          class="block h-[380px] w-full cursor-crosshair select-none md:h-[460px] xl:h-[520px]"
          style="touch-action: none"
          role="img"
          :aria-label="ariaLabel"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
          @pointerleave="onPointerLeave"
          @wheel="onWheel"
        />

        <!-- Rótulos ancorados no fim de cada trajetória: só após o desenho terminar -->
        <span
          v-for="anchor in labelAnchors"
          :key="anchor.key"
          class="num pointer-events-none absolute text-[11px] whitespace-nowrap transition-opacity duration-300"
          :class="[
            { best: 'text-best', base: 'text-ai', worst: 'text-down' }[anchor.key],
            labelsVisible ? 'opacity-100' : 'opacity-0',
          ]"
          :style="{ left: `${anchor.x}px`, top: `${anchor.y - 8}px` }"
          aria-hidden="true"
        >
          <template v-if="highlightSummary?.[anchor.key]">
            {{ { best: 'MELHOR', base: 'BASE', worst: 'PIOR' }[anchor.key] }} ·
            {{ formatNumber(highlightSummary[anchor.key]!.value, 0) }} ·
            {{ formatPercent(highlightSummary[anchor.key]!.change) }}
          </template>
        </span>

        <!-- Tooltip do crosshair (a tabela alternativa é o caminho acessível) -->
        <div
          v-if="tooltip"
          class="cf-surface pointer-events-none absolute w-[186px] px-3 py-2.5"
          :style="tooltipStyle"
          aria-hidden="true"
        >
          <p class="num text-[11px] text-dimmed">
            {{ tooltip.time === null ? '—' : formatUtcShort(tooltip.time * 1000, { withTime: false, withYear: true }).toUpperCase() }}
          </p>
          <p
            v-if="tooltip.best"
            class="num mt-1.5 flex justify-between gap-3 text-[11px] text-best"
          >
            <span>MELHOR</span><span>{{ formatNumber(tooltip.best.value, 0) }}</span>
          </p>
          <p
            v-if="tooltip.base"
            class="num mt-1 flex justify-between gap-3 text-[11px] text-ai"
          >
            <span>BASE</span><span>{{ formatNumber(tooltip.base.value, 0) }}</span>
          </p>
          <p
            v-if="tooltip.worst"
            class="num mt-1 flex justify-between gap-3 text-[11px] text-down"
          >
            <span>PIOR</span><span>{{ formatNumber(tooltip.worst.value, 0) }}</span>
          </p>
        </div>
      </div>

      <!-- Legenda + controles acessíveis -->
      <div class="cf-hairline-t mt-4 flex flex-wrap items-center justify-between gap-x-6 gap-y-3 pt-3">
        <div class="flex flex-wrap items-center gap-x-5 gap-y-2">
          <span class="num inline-flex items-center gap-2 text-[11px] text-muted">
            <span
              class="inline-block h-[2px] w-5 bg-[var(--cf-best)]"
              aria-hidden="true"
            />Melhor cenário
          </span>
          <span class="num inline-flex items-center gap-2 text-[11px] text-muted">
            <span
              class="inline-block h-[2px] w-5 bg-[var(--cf-cyan)]"
              aria-hidden="true"
            />Cenário base
          </span>
          <span class="num inline-flex items-center gap-2 text-[11px] text-muted">
            <span
              class="inline-block h-[2px] w-5 bg-[var(--cf-down)]"
              aria-hidden="true"
            />Pior cenário
          </span>
          <span class="num text-[11px] text-dimmed">
            {{ formatNumber(prepared.simulatedCount, 0) }} trajetórias simuladas
            <template v-if="prepared.drawn.length < prepared.paths.length">
              · {{ formatNumber(prepared.drawn.length, 0) }} desenhadas
            </template>
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-x-3 gap-y-2">
          <div
            class="flex items-center gap-0.5"
            role="group"
            aria-label="Navegar na simulação"
          >
            <UButton
              v-for="action in NAV_ACTIONS"
              :key="action.key"
              color="neutral"
              variant="ghost"
              size="xs"
              :icon="action.icon"
              :aria-label="action.label"
              @click="runNav(action.key)"
            />
          </div>
          <UButton
            variant="link"
            color="neutral"
            size="xs"
            class="p-0 text-[11px]"
            label="Ver como tabela"
            icon="i-lucide-table"
            @click="tableOpen = true"
          />
        </div>
      </div>

      <p class="num mt-3 text-[11px] text-dimmed">
        Arraste para explorar · scroll para zoom · eixo em UTC · linha de corte = último dado observado
      </p>

      <UModal
        v-model:open="tableOpen"
        title="Trajetórias destacadas"
        description="Melhor caso, cenário base e pior caso por data. Valores em USDT, datas em UTC."
        :ui="{ content: 'max-w-2xl' }"
      >
        <template #body>
          <div class="max-h-[60dvh] overflow-auto">
            <table class="w-full text-[13px]">
              <thead>
                <tr class="cf-hairline-b">
                  <th
                    scope="col"
                    class="eyebrow py-2 text-start text-dimmed"
                  >
                    Data (UTC)
                  </th>
                  <th
                    scope="col"
                    class="eyebrow py-2 text-end text-dimmed"
                  >
                    Melhor
                  </th>
                  <th
                    scope="col"
                    class="eyebrow py-2 text-end text-dimmed"
                  >
                    Base
                  </th>
                  <th
                    scope="col"
                    class="eyebrow py-2 text-end text-dimmed"
                  >
                    Pior
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in tableRows"
                  :key="row.date"
                  class="cf-rule"
                >
                  <td class="num py-1.5">
                    {{ row.date }}
                  </td>
                  <td class="num py-1.5 text-end text-best">
                    {{ row.best }}
                  </td>
                  <td class="num py-1.5 text-end text-ai">
                    {{ row.base }}
                  </td>
                  <td class="num py-1.5 text-end text-down">
                    {{ row.worst }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </UModal>
    </template>
  </div>
</template>
