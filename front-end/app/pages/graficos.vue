<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { FeatureRow, Kline, Timeframe } from '~/types/api'
import { LIMIT_BY_TF, STALE_AFTER_HOURS_BY_TF, STORAGE_KEYS, symbolName } from '~/utils/constants'
import { latestOpenTime } from '~/utils/chart-mapping'
import { latestSnapshotAt, sortTickers, trackedSymbols } from '~/utils/tickers'
import { formatUtc } from '~/utils/format'

/**
 * Gráficos (Design.md §10): paisagem full-width dentro das margens, dock funcional
 * de indicadores e resumo 24h aberto abaixo. Sem card, sem moldura luminosa.
 */
const { symbol, tf, ensureSymbol } = useDashboardQuery()
const indicators = useIndicatorPrefs()
const hollow = useHollowCandles()
const scenarios = useScenarioPref()
const drawerOpen = useIndicatorsDrawer()
const lastSymbol = useLastSymbol()
const toast = useToast()
const api = useApi()

const symbols = useSymbols()
const tickers = useTickers24h()
const klines = useKlines(symbol, tf)
const features = useFeatures(symbol, tf)

// ---- Ativo inicial: primeiro por volume 24h (fallback alfabético), escrito na URL ----
watch([() => symbols.data.value, () => tickers.status.value], () => {
  if (symbol.value || !symbols.data.value.length) return
  if (tickers.status.value === 'pending') return
  const byVolume = sortTickers(tickers.data.value, 'quote_volume', 'desc').map(t => t.symbol)
  const tracked = trackedSymbols(symbols.data.value)
  const known = new Set(tracked.map(s => s.symbol))
  const first = byVolume.find(s => known.has(s)) ?? tracked[0]?.symbol ?? null
  void ensureSymbol(first)
}, { immediate: true })

// Atalho "Continuar no gráfico" no Início
watch(symbol, (s) => {
  if (s) lastSymbol.value = s
}, { immediate: true })

// ---- Páginas mais antigas (só 1d pode passar de 1000 velas) ----
const olderKlines = ref<Kline[]>([])
const olderFeatures = ref<FeatureRow[]>([])
const loadingOlder = ref(false)
watch([symbol, tf], () => {
  olderKlines.value = []
  olderFeatures.value = []
})
const allKlines = computed(() => (olderKlines.value.length ? [...klines.data.value, ...olderKlines.value] : klines.data.value))
const allFeatures = computed(() => (olderFeatures.value.length ? [...features.data.value, ...olderFeatures.value] : features.data.value))

async function loadOlder() {
  if (loadingOlder.value || !symbol.value || tf.value !== '1d') return
  const oldest = [...allKlines.value].sort((a, b) => Date.parse(a.open_time) - Date.parse(b.open_time))[0]
  if (!oldest) return
  const end = new Date(Date.parse(oldest.open_time) - 1000).toISOString()
  loadingOlder.value = true
  try {
    const [k, f] = await Promise.all([
      api.get('/api/v1/klines/{timeframe}', { params: { path: { timeframe: tf.value }, query: { symbol: symbol.value, limit: LIMIT_BY_TF['1d'], end } } }),
      api.get('/api/v1/features/{timeframe}', { params: { path: { timeframe: tf.value }, query: { symbol: symbol.value, limit: LIMIT_BY_TF['1d'], end } } }),
    ])
    if (!k.length) {
      toast.add({ title: 'Não há velas mais antigas para este ativo.', color: 'neutral' })
      return
    }
    olderKlines.value = [...olderKlines.value, ...k]
    olderFeatures.value = [...olderFeatures.value, ...f]
  } catch {
    toast.add({ title: 'Não foi possível carregar velas mais antigas.', color: 'neutral', icon: 'i-lucide-circle-alert' })
  } finally {
    loadingOlder.value = false
  }
}

// ---- Frescor ----
const lastCandleAt = computed(() => latestOpenTime(klines.data.value))
const klinesFresh = useFreshness('klines', lastCandleAt, () => klines.status.value, () => STALE_AFTER_HOURS_BY_TF[tf.value])
const ticker = computed(() => (symbol.value ? tickers.data.value.find(t => t.symbol === symbol.value) ?? null : null))
const tickerAt = computed(() => (ticker.value ? latestSnapshotAt([ticker.value]) : null))
const tickerFresh = useFreshness('tickers', tickerAt, () => tickers.status.value)

// ---- Atualizar tudo ----
const refreshing = ref(false)
async function refreshAll() {
  if (refreshing.value) return
  refreshing.value = true
  const before = lastCandleAt.value
  try {
    await Promise.all([klines.refresh(), features.refresh(), tickers.refresh(), symbols.refresh()])
    const after = lastCandleAt.value
    if (after && before && after === before) toast.add({ title: `Nenhum snapshot novo desde ${formatUtc(after)}.`, color: 'neutral' })
    else if (after) toast.add({ title: `Dados atualizados. Snapshot de ${formatUtc(after)}.`, color: 'neutral', icon: 'i-lucide-check' })
  } finally {
    refreshing.value = false
  }
}

// ---- Responsivo (Design.md §10) ----
const isDesktop = useMediaQuery('(min-width: 1024px)')
const isMobile = useMediaQuery('(max-width: 767px)')
const collapsibleOpen = ref(false)

// Mobile na 1ª visita: RSI ligado, MACD desligado
onMounted(() => {
  if (isMobile.value && !localStorage.getItem(STORAGE_KEYS.macdMobileDismissed)) {
    indicators.toggle('macd', false)
    indicators.toggle('rsi', true)
    localStorage.setItem(STORAGE_KEYS.macdMobileDismissed, '1')
  }
})

const selectorEl = ref<{ $el?: HTMLElement } | null>(null)
function focusSelector() {
  const el = selectorEl.value?.$el
  const btn = el?.querySelector<HTMLElement>('button')
  btn?.focus()
  btn?.click()
}

const title = computed(() => (symbol.value ? `${symbol.value} · ${tf.value} · CRYPTO FORECASTING` : 'Gráficos · CRYPTO FORECASTING'))
useHead({ title })

function switchTf(next: Timeframe) {
  tf.value = next
}
</script>

<template>
  <div class="cf-gutter cf-shell pt-10 pb-16 md:pt-12 md:pb-20">
    <!-- Cabeçalho + toolbar: ativo, timeframe, snapshot e atualizar -->
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div class="min-w-0">
        <h1 class="cf-h2 uppercase">
          Gráficos
        </h1>
        <p class="num mt-2 truncate text-[13px] text-muted">
          <span translate="no">{{ symbol ?? '—' }}</span>
          <template v-if="symbol && symbolName(symbol)">
            · {{ symbolName(symbol) }}
          </template>
          · velas de {{ tf }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-x-5 gap-y-2 lg:justify-end">
        <SnapshotBadge
          :state="klinesFresh.state.value"
          :label="klinesFresh.label.value"
        />
        <UButton
          color="neutral"
          variant="outline"
          icon="i-lucide-refresh-cw"
          :loading="refreshing"
          :label="refreshing ? 'Atualizando…' : 'Atualizar'"
          aria-label="Atualizar dados"
          @click="refreshAll"
        />
      </div>
    </div>

    <div class="cf-hairline-b mt-5 flex flex-wrap items-center gap-x-6 gap-y-3 pb-4">
      <SymbolSelector
        ref="selectorEl"
        v-model="symbol"
        :symbols="symbols.data.value"
        :tickers="tickers.data.value"
        :status="symbols.status.value"
        @retry="symbols.refresh()"
      />
      <TimeframeToggle v-model="tf" />
      <UButton
        v-if="isMobile"
        class="ms-auto"
        color="neutral"
        variant="outline"
        icon="i-lucide-sliders-horizontal"
        :label="`Indicadores (${indicators.enabledCount.value})`"
        aria-haspopup="dialog"
        :aria-expanded="drawerOpen"
        @click="drawerOpen = true"
      />
    </div>

    <!-- Tablet: indicadores colapsáveis acima do gráfico -->
    <UCollapsible
      v-if="!isDesktop && !isMobile"
      v-model:open="collapsibleOpen"
      class="cf-surface mt-5"
    >
      <UButton
        color="neutral"
        variant="ghost"
        block
        class="justify-between px-4 py-3"
        :label="`Indicadores (${indicators.enabledCount.value} ligados)`"
        :trailing-icon="collapsibleOpen ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
      />
      <template #content>
        <IndicatorToggles
          variant="dock"
          :controller="indicators"
          :features="allFeatures"
          :features-status="features.status.value"
          :scenario="scenarios"
          @retry-features="features.refresh()"
          @toggle-scenario="(v: boolean) => { scenarios = v }"
        />
      </template>
    </UCollapsible>

    <!-- Paisagem + dock -->
    <div class="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_248px] lg:gap-8 xl:grid-cols-[minmax(0,1fr)_280px]">
      <div
        class="min-h-[430px] md:min-h-[520px]"
        style="height: clamp(430px, 62vh, 780px)"
      >
        <ChartPanel
          :symbol="symbol ?? '—'"
          :tf="tf"
          :klines="allKlines"
          :features="allFeatures"
          :klines-status="klines.status.value"
          :klines-error="klines.error.value"
          :features-status="features.status.value"
          :features-error="features.error.value"
          :prefs="indicators.prefs.value"
          :hollow-up="hollow"
          :show-scenarios="scenarios"
          :stale="klinesFresh.isStale.value"
          :hours-late="klinesFresh.hoursLate.value"
          :loading-older="loadingOlder"
          :compact="isMobile"
          @retry="klines.refresh()"
          @retry-features="features.refresh()"
          @load-older="loadOlder"
          @switch-tf="switchTf"
          @pick-symbol="focusSelector"
        />
      </div>

      <aside
        v-if="isDesktop"
        class="cf-surface self-start"
        aria-label="Indicadores"
      >
        <IndicatorToggles
          variant="dock"
          :controller="indicators"
          :features="allFeatures"
          :features-status="features.status.value"
          :scenario="scenarios"
          @retry-features="features.refresh()"
          @toggle-scenario="(v: boolean) => { scenarios = v }"
        />
      </aside>
    </div>

    <!-- Resumo 24h: faixa aberta -->
    <div class="mt-14 md:mt-20">
      <Summary24hStrip
        :symbol="symbol ?? '—'"
        :ticker="ticker"
        :status="tickers.status.value"
        :freshness="{ state: tickerFresh.state.value, atUtc: tickerFresh.atUtc.value, ago: tickerFresh.ago.value }"
        @retry="tickers.refresh()"
      />
    </div>

    <p class="mt-8 max-w-[62ch] text-[13px] text-dimmed">
      Leia as previsões como cenários, não como recomendação de compra ou venda.
    </p>

    <!-- Mobile: drawer inferior de indicadores -->
    <UDrawer
      v-if="isMobile"
      v-model:open="drawerOpen"
      title="Indicadores"
      description="Persistem no navegador."
      :ui="{ content: 'max-h-[85dvh]' }"
    >
      <template #body>
        <IndicatorToggles
          variant="drawer"
          :controller="indicators"
          :features="allFeatures"
          :features-status="features.status.value"
          :scenario="scenarios"
          @retry-features="features.refresh()"
          @toggle-scenario="(v: boolean) => { scenarios = v }"
        />
      </template>
    </UDrawer>
  </div>
</template>
