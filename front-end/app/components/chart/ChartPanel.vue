<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { FeatureRow, Kline, Timeframe } from '~/types/api'
import type { IndicatorPrefs } from '~/composables/useIndicatorPrefs'
import type { ScenarioSet } from '~/utils/chart-mapping'
import type { AsyncStatus } from '~/utils/async-state'
import { asyncView, isRefreshing } from '~/utils/async-state'
import { LIMIT_BY_TF, TIMEFRAME_META, symbolName } from '~/utils/constants'
import { describeError, messageOf } from '~/utils/api-errors'
import { EM_DASH, formatNumber, formatPrice, formatUtcShort } from '~/utils/format'

/**
 * Paisagem do gráfico (Design.md §10): full-width dentro das margens, sem card
 * externo e sem moldura luminosa. Estados preservam a geometria final.
 */
const props = defineProps<{
  symbol: string
  tf: Timeframe
  klines: readonly Kline[]
  features: readonly FeatureRow[]
  klinesStatus: AsyncStatus
  klinesError: unknown
  featuresStatus: AsyncStatus
  featuresError: unknown
  prefs: IndicatorPrefs
  hollowUp: boolean
  scenarios?: ScenarioSet | null
  showScenarios?: boolean
  stale: boolean
  hoursLate: number
  loadingOlder: boolean
  compact?: boolean
}>()

const emit = defineEmits<{
  'retry': []
  'retry-features': []
  'load-older': []
  'switch-tf': [tf: Timeframe]
  'pick-symbol': []
}>()

const tableOpen = ref(false)
const hasData = computed(() => props.klines.length > 0)

const view = computed(() => asyncView(props.klinesStatus, hasData.value))
const refreshing = computed(() => isRefreshing(props.klinesStatus, hasData.value))

const meta = computed(() => TIMEFRAME_META[props.tf])
const canLoadOlder = computed(() => props.tf === '1d' && props.klines.length >= LIMIT_BY_TF['1d'])
const countLabel = computed(() => `${formatNumber(props.klines.length, 0)} velas · ${meta.value.retention}`)
const altTf = computed<Timeframe>(() => (props.tf === '1d' ? '1h' : '1d'))
const panes = computed(() => 1 + (props.prefs.rsi ? 1 : 0) + (props.prefs.macd ? 1 : 0))

/** Nenhuma trajetória real do modelo: a área depois da linha de corte fica reservada. */
const hasScenarios = computed(() => Boolean(
  props.showScenarios && props.scenarios
  && (props.scenarios.best.length || props.scenarios.expected.length || props.scenarios.worst.length),
))

// ---- Controles de pan/zoom acessíveis (Design.md §14.2) ----
interface ChartHandle {
  fitContent: () => void
  panLeft: () => void
  panRight: () => void
  zoomIn: () => void
  zoomOut: () => void
}
const chartRef = ref<ChartHandle | null>(null)

const NAV_ACTIONS = [
  { key: 'panLeft', icon: 'i-lucide-chevron-left', label: 'Deslocar para trás' },
  { key: 'panRight', icon: 'i-lucide-chevron-right', label: 'Deslocar para frente' },
  { key: 'zoomOut', icon: 'i-lucide-minus', label: 'Afastar' },
  { key: 'zoomIn', icon: 'i-lucide-plus', label: 'Aproximar' },
  { key: 'fitContent', icon: 'i-lucide-maximize-2', label: 'Enquadrar tudo' },
] as const

function runNav(key: (typeof NAV_ACTIONS)[number]['key']) {
  chartRef.value?.[key]()
}

// ---- Tabela alternativa (Design.md §14.2) ----
interface TableRow { open_time: string, open: number, high: number, low: number, close: number, volume: number, sma_20: number | null, sma_50: number | null, rsi_14: number | null, macd: number | null }
const tableRows = computed<TableRow[]>(() => {
  const byTime = new Map(props.features.map(f => [Date.parse(f.timestamp), f]))
  return [...props.klines]
    .sort((a, b) => Date.parse(b.open_time) - Date.parse(a.open_time))
    .slice(0, 50)
    .map((k) => {
      const f = byTime.get(Date.parse(k.open_time))
      return { open_time: k.open_time, open: k.open, high: k.high, low: k.low, close: k.close, volume: k.volume, sma_20: f?.sma_20 ?? null, sma_50: f?.sma_50 ?? null, rsi_14: f?.rsi_14 ?? null, macd: f?.macd ?? null }
    })
})
const num = { class: { th: 'text-right', td: 'text-right num' } }
const tableColumns: TableColumn<TableRow>[] = [
  { accessorKey: 'open_time', header: 'Abertura (UTC)', cell: ({ row }) => formatUtcShort(row.original.open_time, { withYear: props.tf === '1d', withTime: props.tf !== '1d' }), meta: { class: { td: 'num' } } },
  { accessorKey: 'open', header: 'A', cell: ({ row }) => formatPrice(row.original.open), meta: num },
  { accessorKey: 'high', header: 'M', cell: ({ row }) => formatPrice(row.original.high), meta: num },
  { accessorKey: 'low', header: 'm', cell: ({ row }) => formatPrice(row.original.low), meta: num },
  { accessorKey: 'close', header: 'F', cell: ({ row }) => formatPrice(row.original.close), meta: num },
  { accessorKey: 'volume', header: 'Vol', cell: ({ row }) => formatNumber(row.original.volume, 1), meta: num },
  { accessorKey: 'sma_20', header: 'SMA 20', cell: ({ row }) => formatPrice(row.original.sma_20), meta: num },
  { accessorKey: 'sma_50', header: 'SMA 50', cell: ({ row }) => formatPrice(row.original.sma_50), meta: num },
  { accessorKey: 'rsi_14', header: 'RSI 14', cell: ({ row }) => (row.original.rsi_14 === null ? EM_DASH : formatNumber(row.original.rsi_14, 1)), meta: num },
  { accessorKey: 'macd', header: 'MACD', cell: ({ row }) => formatPrice(row.original.macd), meta: num },
]

const errorDetail = computed(() => describeError(props.klinesError))
const errorMessage = computed(() => messageOf(props.klinesError))
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <!-- Aviso de dados velhos: inline, sem bloquear o gráfico (Design.md §13.2) -->
    <p
      v-if="props.stale && view === 'ready'"
      class="cf-surface mb-3 flex flex-wrap items-center gap-x-2.5 gap-y-1 px-3.5 py-2.5 text-[13px] text-warn"
      role="status"
    >
      <UIcon
        name="i-lucide-triangle-alert"
        class="size-4 shrink-0"
        aria-hidden="true"
      />
      <span class="text-hi">Dados mais antigos que o esperado.</span>
      <span class="text-muted">Os candles deveriam ter sido atualizados há ~{{ props.hoursLate }} h (00:05 UTC). O gráfico continua utilizável.</span>
      <UButton
        variant="link"
        size="xs"
        class="p-0 text-warn"
        label="Tentar novamente"
        @click="emit('retry')"
      />
    </p>

    <div class="relative min-h-0 flex-1">
      <!-- Indicadores falharam: os candles seguem (Design.md §13.2) -->
      <p
        v-if="view === 'ready' && props.featuresStatus === 'error'"
        class="cf-surface absolute top-3 right-3 z-10 flex items-center gap-2 px-3 py-2 text-[13px] text-muted"
        role="alert"
      >
        Indicadores não carregaram.
        <UButton
          variant="link"
          size="xs"
          label="Tentar novamente"
          class="p-0"
          @click="emit('retry-features')"
        />
      </p>

      <ChartSkeleton
        v-if="view === 'loading' || view === 'idle'"
        :label="`Carregando ${props.symbol} · ${props.tf}…`"
        :panes="panes"
      />

      <EmptyState
        v-else-if="view === 'empty'"
        :title="`Sem dados para ${props.symbol} em ${props.tf}`"
        description="Este ativo está na lista dos top 20, mas ainda não tem candles neste timeframe. Tente outro timeframe ou volte depois da próxima coleta (00:05 UTC)."
        :actions="[
          { label: `Ver em ${altTf}`, color: 'neutral', variant: 'outline', onClick: () => emit('switch-tf', altTf) },
          { label: 'Escolher outro ativo', color: 'neutral', variant: 'ghost', onClick: () => emit('pick-symbol') },
        ]"
      />

      <ErrorState
        v-else-if="view === 'error'"
        title="Não foi possível carregar o gráfico"
        :description="errorMessage"
        :detail="errorDetail"
        :retrying="props.klinesStatus === 'pending'"
        @retry="emit('retry')"
      />

      <div
        v-else
        class="h-full transition-opacity duration-200"
        :class="refreshing ? 'opacity-55' : ''"
        :aria-busy="refreshing"
      >
        <ClientOnly>
          <ChartCandlestickChart
            ref="chartRef"
            :symbol="props.symbol"
            :tf="props.tf"
            :klines="props.klines"
            :features="props.features"
            :prefs="props.prefs"
            :hollow-up="props.hollowUp"
            :scenarios="props.scenarios"
            :show-scenarios="props.showScenarios"
            :compact="props.compact"
            @reach-left-edge="canLoadOlder && emit('load-older')"
          />
          <template #fallback>
            <ChartSkeleton
              :label="`Carregando ${props.symbol} · ${props.tf}…`"
              :panes="panes"
            />
          </template>
        </ClientOnly>

        <div
          v-if="canLoadOlder"
          class="absolute top-1/2 left-2 z-10 -translate-y-1/2"
        >
          <UButton
            color="neutral"
            variant="outline"
            size="xs"
            icon="i-lucide-chevrons-left"
            label="Carregar mais antigo"
            :loading="props.loadingOlder"
            @click="emit('load-older')"
          />
        </div>
      </div>
    </div>

    <!-- Rodapé de interação (Design.md §10) -->
    <div class="cf-hairline-t mt-3 flex flex-wrap items-center justify-between gap-x-5 gap-y-2 pt-3">
      <p class="num text-[11px] text-dimmed">
        Eixo em UTC · arraste para navegar · scroll para zoom · linha de corte = último dado observado
      </p>

      <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div
          v-if="view === 'ready'"
          class="flex items-center gap-0.5"
          role="group"
          aria-label="Navegar no gráfico"
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
        <span class="num text-[11px] text-dimmed">{{ countLabel }}</span>
        <UButton
          v-if="hasData"
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

    <!-- Área reservada à previsão: estado honesto, nunca números fabricados -->
    <p
      v-if="view === 'ready' && !hasScenarios"
      class="num mt-2 text-[11px] text-dimmed"
    >
      O modelo ainda não publicou previsões para este ativo.
    </p>

    <UModal
      v-model:open="tableOpen"
      :title="`${props.symbol} · ${props.tf} · últimas 50 velas`"
      :description="`${symbolName(props.symbol) ?? props.symbol} — OHLCV e indicadores, do mais recente ao mais antigo. Horários em UTC.`"
      :ui="{ content: 'max-w-4xl' }"
    >
      <template #body>
        <div class="overflow-x-auto">
          <UTable
            :data="tableRows"
            :columns="tableColumns"
            class="text-[12px]"
            :ui="{ th: 'eyebrow text-dimmed py-2', td: 'py-1.5 whitespace-nowrap' }"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
