<script setup lang="ts">
/**
 * Gráfico de candles (Lightweight Charts v5) — só cliente.
 * Pane 0: candles + volume (escala própria) + overlays (SMA/EMA/BB). Pane RSI e pane MACD opcionais.
 * Linha de corte + área reservada à previsão à direita (ux-spec §4.2). Legenda HTML sobreposta.
 */
import {
  BaselineSeries,
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  LineStyle,
  TickMarkType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LineWidth,
  type LogicalRange,
  type MouseEventParams,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts'
import type { FeatureKey, FeatureRow, Kline, Timeframe } from '~/types/api'
import type { IndicatorPrefs } from '~/composables/useIndicatorPrefs'
import { CANDLE_COLORS, INDICATOR_BY_KEY, INDICATOR_DEFS, MACD_SIGNAL_COLOR, TIMEFRAME_META, type LineStyleName } from '~/utils/constants'
import { featureToHistogram, featureToLine, klinesToCandles, klinesToVolume, lastValue, valueAt, warmupInfo } from '~/utils/chart-mapping'
import { EM_DASH, formatNumber, formatPrice, formatUtcShort, priceDecimals } from '~/utils/format'

const props = defineProps<{
  symbol: string
  tf: Timeframe
  klines: readonly Kline[]
  features: readonly FeatureRow[]
  prefs: IndicatorPrefs
  hollowUp?: boolean
  /** Sem linha de corte/área reservada (ex.: telas muito estreitas). */
  compact?: boolean
}>()

const emit = defineEmits<{ (e: 'reach-left-edge'): void }>()

const container = ref<HTMLDivElement | null>(null)

let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
const overlaySeries = new Map<string, ISeriesApi<'Line'>>()
let rsiSeries: ISeriesApi<'Line'> | null = null
let rsiBand: ISeriesApi<'Baseline'> | null = null
let macdLine: ISeriesApi<'Line'> | null = null
let macdSignal: ISeriesApi<'Line'> | null = null
let macdHist: ISeriesApi<'Histogram'> | null = null
let edgeNotified = false

const candles = computed(() => klinesToCandles(props.klines))
const lastCandle = computed(() => candles.value.at(-1) ?? null)
const lastTime = computed(() => lastCandle.value?.time ?? null)
const precision = computed(() => priceDecimals(lastCandle.value?.close ?? 1))

const palette = CANDLE_COLORS

/** Lê tokens CSS do tema atual (layout do gráfico segue o chrome). */
function cssVar(name: string, fallback: string): string {
  if (!container.value) return fallback
  const v = getComputedStyle(container.value).getPropertyValue(name).trim()
  return v || fallback
}

function lineStyleOf(name: LineStyleName): LineStyle {
  if (name === 'dashed') return LineStyle.Dashed
  if (name === 'dotted') return LineStyle.Dotted
  return LineStyle.Solid
}

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
function tickMarkFormatter(time: Time, type: TickMarkType): string | null {
  if (typeof time !== 'number') return null
  const d = new Date(time * 1000)
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  switch (type) {
    case TickMarkType.Year: return String(d.getUTCFullYear())
    case TickMarkType.Month: return MONTHS[d.getUTCMonth()] ?? null
    case TickMarkType.DayOfMonth: return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`
    default: return `${hh}:${mm}`
  }
}

function timeFormatter(time: Time): string {
  if (typeof time !== 'number') return ''
  return props.tf === '1d' ? formatUtcShort(time * 1000, { withTime: false, withYear: true }) : formatUtcShort(time * 1000)
}

function chartOptions() {
  return {
    autoSize: true,
    layout: {
      background: { type: ColorType.Solid, color: 'transparent' },
      textColor: cssVar('--ui-text-dimmed', '#66788f'),
      fontFamily: '"Google Sans Code", ui-monospace, monospace',
      fontSize: 11,
      panes: { separatorColor: cssVar('--ui-border', 'rgba(216,230,245,.14)'), separatorHoverColor: 'rgba(62,134,247,.15)', enableResize: true },
    },
    grid: {
      vertLines: { visible: false },
      horzLines: { color: cssVar('--ui-border-muted', 'rgba(216,230,245,.08)') },
    },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: { color: cssVar('--ui-text-dimmed', '#66788f'), style: LineStyle.Dashed, width: 1 as const, labelBackgroundColor: cssVar('--cf-solid', '#0c1626') },
      horzLine: { color: cssVar('--ui-text-dimmed', '#66788f'), style: LineStyle.Dashed, width: 1 as const, labelBackgroundColor: cssVar('--cf-solid', '#0c1626') },
    },
    rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.08, bottom: 0.22 } },
    timeScale: {
      borderVisible: false,
      timeVisible: props.tf !== '1d',
      secondsVisible: false,
      rightOffset: props.compact ? 3 : 14,
      tickMarkFormatter,
    },
    localization: { locale: 'pt-BR', timeFormatter },
    handleScroll: { vertTouchDrag: false },
  }
}

function buildChart() {
  if (!container.value) return
  chart = createChart(container.value, chartOptions())
  chart.subscribeCrosshairMove(onCrosshair)
  chart.timeScale().subscribeVisibleLogicalRangeChange(onRangeChange)
  buildSeries()
}

function clearSeries() {
  if (!chart) return
  for (const s of overlaySeries.values()) chart.removeSeries(s)
  overlaySeries.clear()
  for (const s of [rsiSeries, rsiBand, macdLine, macdSignal, macdHist, volumeSeries, candleSeries]) {
    if (s) chart.removeSeries(s as ISeriesApi<'Line'>)
  }
  rsiSeries = rsiBand = macdLine = macdSignal = macdHist = null
  volumeSeries = null
  candleSeries = null
  // Panes vazios que sobraram
  while (chart.panes().length > 1) chart.removePane(chart.panes().length - 1)
}

function buildSeries() {
  if (!chart) return
  const p = palette
  const prefs = props.prefs

  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: props.hollowUp ? p.upBody : p.up,
    downColor: p.down,
    borderUpColor: p.up,
    borderDownColor: p.down,
    wickUpColor: p.up,
    wickDownColor: p.down,
    borderVisible: true,
    priceLineVisible: false,
    lastValueVisible: true,
    priceFormat: { type: 'custom', formatter: (v: number) => formatPrice(v), minMove: 1 / 10 ** precision.value },
  }, 0)
  candleSeries.setData(candles.value)

  if (prefs.volume) {
    volumeSeries = chart.addSeries(HistogramSeries, {
      priceScaleId: 'volume',
      priceFormat: { type: 'volume' },
      priceLineVisible: false,
      lastValueVisible: false,
    }, 0)
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } })
    volumeSeries.setData(klinesToVolume(props.klines, { up: p.upSoft, down: p.downSoft }))
  }

  for (const def of INDICATOR_DEFS) {
    if (def.pane !== 'price' || !prefs[def.key]) continue
    for (const field of def.fields) {
      const isMiddle = field === 'bb_middle'
      const s = chart.addSeries(LineSeries, {
        color: def.color,
        lineWidth: def.lineWidth as LineWidth,
        lineStyle: isMiddle ? LineStyle.Dashed : lineStyleOf(def.lineStyle),
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
        priceFormat: { type: 'custom', formatter: (v: number) => formatPrice(v), minMove: 1 / 10 ** precision.value },
      }, 0)
      s.setData(featureToLine(props.features, field))
      overlaySeries.set(field, s)
    }
  }

  let paneIndex = 1
  if (prefs.rsi) {
    const def = INDICATOR_BY_KEY.rsi
    rsiBand = chart.addSeries(BaselineSeries, {
      baseValue: { type: 'price', price: 30 },
      topFillColor1: 'rgba(62,134,247,.06)',
      topFillColor2: 'rgba(62,134,247,.06)',
      topLineColor: 'transparent',
      bottomFillColor1: 'transparent',
      bottomFillColor2: 'transparent',
      bottomLineColor: 'transparent',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    }, paneIndex)
    rsiBand.setData(candles.value.map(c => ({ time: c.time, value: 70 })))
    rsiSeries = chart.addSeries(LineSeries, {
      color: def.color,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
      priceFormat: { type: 'custom', formatter: (v: number) => formatNumber(v, 0), minMove: 1 },
      autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
    }, paneIndex)
    rsiSeries.setData(featureToLine(props.features, 'rsi_14'))
    const border = cssVar('--ui-border', 'rgba(216,230,245,.14)')
    for (const price of [30, 70]) {
      rsiSeries.createPriceLine({ price, color: border, lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: true, title: '' })
    }
    paneIndex++
  }

  if (prefs.macd) {
    const def = INDICATOR_BY_KEY.macd
    const macdFormat = { type: 'custom' as const, formatter: (v: number) => formatPrice(v), minMove: 1 / 10 ** precision.value }
    macdHist = chart.addSeries(HistogramSeries, {
      priceLineVisible: false,
      lastValueVisible: false,
      base: 0,
      priceFormat: macdFormat,
    }, paneIndex)
    macdHist.setData(featureToHistogram(props.features, 'macd_histogram', { positive: p.upHist, negative: p.downHist }))
    macdLine = chart.addSeries(LineSeries, { color: def.color, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: macdFormat }, paneIndex)
    macdLine.setData(featureToLine(props.features, 'macd'))
    macdSignal = chart.addSeries(LineSeries, { color: MACD_SIGNAL_COLOR, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false, priceFormat: macdFormat }, paneIndex)
    macdSignal.setData(featureToLine(props.features, 'macd_signal'))
    paneIndex++
  }

  applyPaneSizes()
  updateCutLine()
}

function applyPaneSizes() {
  if (!chart) return
  const panes = chart.panes()
  const below = panes.length - 1
  if (below === 0) {
    panes[0]?.setStretchFactor(1)
    return
  }
  panes[0]?.setStretchFactor(below === 1 ? 0.72 : 0.56)
  for (let i = 1; i < panes.length; i++) panes[i]?.setStretchFactor(below === 1 ? 0.28 : 0.22)
}

/** Reconstrói séries preservando a janela visível (toggle, tema, dados). */
function rebuild() {
  if (!chart) return
  const range = chart.timeScale().getVisibleLogicalRange()
  clearSeries()
  chart.applyOptions(chartOptions())
  buildSeries()
  if (range) chart.timeScale().setVisibleLogicalRange(range)
}

function updateData() {
  if (!chart || !candleSeries) return
  rebuild()
  // Novo ativo/timeframe: enquadra as últimas ~120 velas com folga à direita.
  const n = candles.value.length
  if (n > 0) {
    const visible = Math.min(n, props.compact ? 60 : 120)
    chart.timeScale().setVisibleLogicalRange({ from: n - visible - 0.5, to: n - 0.5 + (props.compact ? 3 : 14) })
  }
  edgeNotified = false
}

// ---------- Linha de corte / área reservada ----------
const cutLeft = ref<number | null>(null)
const priceScaleWidth = ref(0)
function updateCutLine() {
  if (!chart || lastTime.value === null || props.compact) {
    cutLeft.value = null
    return
  }
  const x = chart.timeScale().timeToCoordinate(lastTime.value)
  priceScaleWidth.value = chart.priceScale('right').width()
  if (x === null) {
    cutLeft.value = null
    return
  }
  // Metade de uma vela à direita do centro da última vela
  cutLeft.value = x + chart.timeScale().options().barSpacing / 2
}

function onRangeChange(range: LogicalRange | null) {
  updateCutLine()
  measurePanes()
  if (range && range.from <= 2 && !edgeNotified && candles.value.length > 0) {
    edgeNotified = true
    emit('reach-left-edge')
  }
}

// ---------- Legenda ----------
interface LegendRow { key: string, label: string, color: string, style: LineStyleName, value: string, note?: string }
const legendTime = ref<UTCTimestamp | null>(null)
const ohlc = ref<{ open: number, high: number, low: number, close: number, volume: number | null } | null>(null)
const overlayRows = ref<LegendRow[]>([])
const rsiValue = ref<string>(EM_DASH)
const macdValues = ref<{ macd: string, signal: string, hist: string }>({ macd: EM_DASH, signal: EM_DASH, hist: EM_DASH })

function warmupNote(field: FeatureKey, window?: number): string | undefined {
  const info = warmupInfo(props.features, field, window)
  if (info.hasAnyValue && info.firstValueAt) return `warm-up até ${formatUtcShort(info.firstValueAt, { withTime: false })}`
  if (!info.hasAnyValue && info.missing !== null) return `warm-up · faltam ${info.missing} velas`
  return undefined
}

function refreshLegend(time: UTCTimestamp | null) {
  const t = time ?? lastTime.value
  legendTime.value = t
  const candle = t === null ? null : candles.value.find(c => c.time === t) ?? null
  const kline = candle ? props.klines.find(k => Date.parse(k.open_time) / 1000 === candle.time) : undefined
  ohlc.value = candle ? { ...candle, volume: kline?.volume ?? null } : null

  const rows: LegendRow[] = []
  for (const def of INDICATOR_DEFS) {
    if (def.pane !== 'price' || !props.prefs[def.key]) continue
    const field = def.fields[0]
    if (!field) continue
    const v = t === null ? lastValue(props.features, field) : (time === null ? lastValue(props.features, field) : valueAt(props.features, field, t))
    const row: LegendRow = { key: def.key, label: def.label, color: def.color, style: def.lineStyle, value: v === null ? EM_DASH : formatNumber(v, precision.value) }
    if (v === null) row.note = warmupNote(field, def.window)
    rows.push(row)
  }
  overlayRows.value = rows

  const pick = (field: FeatureKey) => (t === null ? null : (time === null ? lastValue(props.features, field) : valueAt(props.features, field, t)))
  const rsi = pick('rsi_14')
  rsiValue.value = rsi === null ? EM_DASH : formatNumber(rsi, 1)
  const mv = pick('macd')
  const ms = pick('macd_signal')
  const mh = pick('macd_histogram')
  macdValues.value = {
    macd: mv === null ? EM_DASH : formatNumber(mv, precision.value, { sign: true }),
    signal: ms === null ? EM_DASH : formatNumber(ms, precision.value, { sign: true }),
    hist: mh === null ? EM_DASH : formatNumber(mh, precision.value, { sign: true }),
  }
}

function onCrosshair(param: MouseEventParams<Time>) {
  const t = typeof param.time === 'number' ? (param.time as UTCTimestamp) : null
  refreshLegend(t)
}

const closeTone = computed(() => (ohlc.value ? (ohlc.value.close >= ohlc.value.open ? 'text-up' : 'text-down') : ''))

// Posição vertical dos painéis (legendas de RSI/MACD)
const paneTops = ref<number[]>([])
function measurePanes() {
  if (!chart || !container.value) return
  const base = container.value.getBoundingClientRect().top
  const tops: number[] = []
  let acc = 0
  for (const pane of chart.panes()) {
    const el = pane.getHTMLElement()
    if (el) {
      tops.push(el.getBoundingClientRect().top - base)
    } else {
      tops.push(acc)
    }
    acc += pane.getHeight() + 1
  }
  paneTops.value = tops
}
function scheduleMeasure() {
  requestAnimationFrame(() => {
    measurePanes()
    setTimeout(measurePanes, 60)
  })
}

// ---------- Ciclo de vida ----------
let ro: ResizeObserver | null = null
onMounted(() => {
  buildChart()
  updateData()
  refreshLegend(null)
  scheduleMeasure()
  ro = new ResizeObserver(() => {
    updateCutLine()
    measurePanes()
  })
  if (container.value) ro.observe(container.value)
})

onBeforeUnmount(() => {
  ro?.disconnect()
  if (chart) {
    chart.unsubscribeCrosshairMove(onCrosshair)
    chart.timeScale().unsubscribeVisibleLogicalRangeChange(onRangeChange)
    chart.remove()
    chart = null
  }
})

watch(() => [props.symbol, props.tf, props.klines, props.features], () => {
  updateData()
  refreshLegend(null)
  scheduleMeasure()
}, { deep: false })

watch(() => [props.prefs, props.hollowUp], () => {
  rebuild()
  refreshLegend(null)
  scheduleMeasure()
}, { deep: true })

const ariaLabel = computed(() => {
  const n = candles.value.length
  const first = candles.value[0]
  const last = lastCandle.value
  const enabled = INDICATOR_DEFS.filter(d => props.prefs[d.key] && d.key !== 'volume').map(d => d.label).join(', ')
  if (!n || !first || !last) return `Gráfico de candles ${props.symbol} ${props.tf}, sem dados`
  return `Gráfico de candles ${props.symbol} ${props.tf}, ${n} velas, de ${formatUtcShort(first.time * 1000, { withTime: false })} a ${formatUtcShort(last.time * 1000, { withTime: false, withYear: true })} UTC${enabled ? `, com ${enabled}` : ''}. Dados até ${formatUtcShort(last.time * 1000)} UTC.`
})

const tfLabel = computed(() => TIMEFRAME_META[props.tf].label)

defineExpose({ fitContent: () => chart?.timeScale().fitContent() })
</script>

<template>
  <div
    class="relative h-full w-full"
    role="img"
    :aria-label="ariaLabel"
  >
    <div
      ref="container"
      class="h-full w-full"
      style="touch-action: none"
    />

    <!-- Linha de corte + área reservada à previsão -->
    <div
      v-if="cutLeft !== null"
      class="pointer-events-none absolute top-0 bottom-0"
      :style="{ left: `${cutLeft}px`, right: `${priceScaleWidth}px` }"
      aria-hidden="true"
    >
      <div
        class="absolute inset-y-0 left-0 border-l border-dashed"
        style="border-color: rgba(95,196,255,.7)"
      />
      <div
        class="absolute inset-y-0 left-0 right-0 opacity-60"
        style="background: repeating-linear-gradient(135deg, transparent 0 6px, var(--cf-forecast-fill) 6px 7px)"
      />
      <span
        class="num text-ai absolute right-2 whitespace-nowrap text-[11px]"
        :style="{ top: `${(paneTops[1] ?? (container?.clientHeight ?? 0) - 30) - 26}px`, textShadow: '0 0 4px var(--ui-bg-elevated)' }"
      >previsão · em breve</span>
    </div>

    <!-- Legenda pane 0 -->
    <div
      class="pointer-events-none absolute left-3 top-2 max-w-[calc(100%-80px)] text-[12px] leading-5"
      aria-hidden="true"
    >
      <div class="num flex flex-wrap items-center gap-x-2 text-default">
        <span
          class="font-semibold text-highlighted"
          translate="no"
        >{{ props.symbol }}</span>
        <span class="text-dimmed">·</span>
        <span>{{ tfLabel }}</span>
        <span class="text-dimmed">·</span>
        <span class="text-muted">{{ legendTime !== null ? formatUtcShort(legendTime * 1000, { withTime: props.tf !== '1d', withYear: props.tf === '1d' }) + ' UTC' : EM_DASH }}</span>
        <template v-if="ohlc">
          <span><span class="text-dimmed">A</span> {{ formatPrice(ohlc.open) }}</span>
          <span><span class="text-dimmed">M</span> {{ formatPrice(ohlc.high) }}</span>
          <span><span class="text-dimmed">m</span> {{ formatPrice(ohlc.low) }}</span>
          <span :class="closeTone"><span class="text-dimmed">F</span> {{ formatPrice(ohlc.close) }}</span>
          <span v-if="ohlc.volume !== null"><span class="text-dimmed">Vol</span> {{ formatNumber(ohlc.volume, 1) }}</span>
        </template>
      </div>
      <div
        v-if="overlayRows.length"
        class="num mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5"
      >
        <span
          v-for="row in overlayRows"
          :key="row.key"
          class="inline-flex items-center gap-1.5"
        >
          <ChartSwatch
            :color="row.color"
            :style-name="row.style"
          />
          <span class="text-muted">{{ row.label }}</span>
          <span class="text-default">{{ row.value }}</span>
          <span
            v-if="row.note"
            class="text-dimmed"
          >{{ row.note }}</span>
        </span>
      </div>
    </div>

    <!-- Legendas dos painéis abaixo -->
    <template v-if="props.prefs.rsi && paneTops[1] !== undefined">
      <div
        class="num pointer-events-none absolute left-3 text-[11px] leading-4"
        :style="{ top: `${paneTops[1] + 6}px` }"
        aria-hidden="true"
      >
        <span class="text-muted">RSI 14</span>
        <span class="ml-1.5 text-primary">{{ rsiValue }}</span>
      </div>
    </template>
    <template v-if="props.prefs.macd && paneTops[props.prefs.rsi ? 2 : 1] !== undefined">
      <div
        class="num pointer-events-none absolute left-3 text-[11px] leading-4"
        :style="{ top: `${(paneTops[props.prefs.rsi ? 2 : 1] ?? 0) + 6}px` }"
        aria-hidden="true"
      >
        <span class="text-muted">MACD 12·26·9</span>
        <span
          class="ml-1.5"
          :style="{ color: INDICATOR_BY_KEY.macd.color }"
        >{{ macdValues.macd }}</span>
        <span
          class="ml-1.5"
          :style="{ color: MACD_SIGNAL_COLOR }"
        >{{ macdValues.signal }}</span>
        <span class="ml-1.5 text-muted">{{ macdValues.hist }}</span>
      </div>
    </template>
  </div>
</template>
