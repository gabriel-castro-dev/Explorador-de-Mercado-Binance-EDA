<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { FeatureRow, Kline, Timeframe } from '~/types/api'
import { LIMIT_BY_TF, STALE_AFTER_HOURS_BY_TF, STORAGE_KEYS, symbolName } from '~/utils/constants'
import { latestOpenTime } from '~/utils/chart-mapping'
import { latestSnapshotAt, sortTickers } from '~/utils/tickers'
import { formatUtc } from '~/utils/format'

useHead({ title: 'Dashboard · crypto forecasting' })

const { symbol, tf, ensureSymbol } = useDashboardQuery()
const indicators = useIndicatorPrefs()
const hollow = useHollowCandles()
const onboarded = useOnboarded()
const drawerOpen = useIndicatorsDrawer()
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
  const known = new Set(symbols.data.value.map(s => s.symbol))
  const first = byVolume.find(s => known.has(s)) ?? symbols.data.value[0]?.symbol ?? null
  void ensureSymbol(first)
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

// ---- Responsivo ----
const isDesktop = useMediaQuery('(min-width: 1024px)')
const isMobile = useMediaQuery('(max-width: 767px)')
const collapsibleOpen = ref(false)

// Mobile na 1ª visita: MACD desligado por padrão (ux-spec §8)
onMounted(() => {
  if (isMobile.value && !localStorage.getItem(STORAGE_KEYS.macdMobileDismissed)) {
    indicators.toggle('macd', false)
    localStorage.setItem(STORAGE_KEYS.macdMobileDismissed, '1')
  }
})

// ---- Onboarding ----
const showHint = computed(() => !onboarded.value && !!symbol.value && klines.status.value === 'success' && klines.data.value.length > 0)
function dismissHint() {
  onboarded.value = true
}

const selectorEl = ref<{ $el?: HTMLElement } | null>(null)
function focusSelector() {
  const el = selectorEl.value?.$el
  const btn = el?.querySelector<HTMLElement>('button')
  btn?.focus()
  btn?.click()
}

const title = computed(() => (symbol.value ? `${symbol.value} · ${tf.value} · crypto forecasting` : 'Dashboard · crypto forecasting'))
useHead({ title })

function switchTf(next: Timeframe) {
  tf.value = next
}
</script>

<template>
  <div class="space-y-4">
    <h1 class="sr-only">
      Dashboard
    </h1>

    <!-- Toolbar -->
    <div class="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center md:justify-between">
      <div class="flex flex-wrap items-center gap-3">
        <SymbolSelector
          ref="selectorEl"
          v-model="symbol"
          :symbols="symbols.data.value"
          :tickers="tickers.data.value"
          :status="symbols.status.value"
          @retry="symbols.refresh()"
        />
        <TimeframeToggle v-model="tf" />
      </div>
      <div class="flex flex-wrap items-center gap-2 md:justify-end">
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

    <!-- Tablet: painel colapsável acima do gráfico -->
    <UCollapsible
      v-if="!isDesktop && !isMobile"
      v-model:open="collapsibleOpen"
      class="rounded-lg border border-default bg-elevated"
    >
      <UButton
        color="neutral"
        variant="ghost"
        block
        class="justify-between px-4"
        :label="`Indicadores (${indicators.enabledCount.value} ligados)`"
        :trailing-icon="collapsibleOpen ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
      />
      <template #content>
        <IndicatorToggles
          :controller="indicators"
          :features="allFeatures"
          :features-status="features.status.value"
          @retry-features="features.refresh()"
        />
      </template>
    </UCollapsible>

    <!-- Gráfico + painel lateral -->
    <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_232px] xl:grid-cols-[minmax(0,1fr)_264px]">
      <div
        class="min-h-[430px] md:min-h-[520px]"
        style="height: clamp(430px, 65vh, 820px)"
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
        class="relative flex flex-col gap-3"
        aria-label="Indicadores"
      >
        <OnboardingHint
          v-if="showHint"
          :symbol="symbol ?? ''"
          :tf="tf"
          @dismiss="dismissHint"
        />
        <div class="min-h-[520px] flex-1 rounded-lg border border-default bg-elevated">
          <IndicatorToggles
            :controller="indicators"
            :features="allFeatures"
            :features-status="features.status.value"
            :highlight-key="showHint ? 'sma50' : null"
            @retry-features="features.refresh()"
          />
        </div>
      </aside>
    </div>

    <!-- Resumo 24h do ativo -->
    <Summary24hStrip
      :symbol="symbol ?? '—'"
      :ticker="ticker"
      :status="tickers.status.value"
      :freshness="{ state: tickerFresh.state.value, atUtc: tickerFresh.atUtc.value, ago: tickerFresh.ago.value }"
      @retry="tickers.refresh()"
    />

    <p
      v-if="symbol && symbolName(symbol)"
      class="sr-only"
    >
      {{ symbolName(symbol) }}
    </p>

    <!-- Mobile: drawer de indicadores -->
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
          @retry-features="features.refresh()"
        />
      </template>
    </UDrawer>
  </div>
</template>
