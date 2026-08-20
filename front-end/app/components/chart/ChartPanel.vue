<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { FeatureRow, Kline, Timeframe } from '~/types/api'
import type { IndicatorPrefs } from '~/composables/useIndicatorPrefs'
import { LIMIT_BY_TF, TIMEFRAME_META, symbolName } from '~/utils/constants'
import { describeError, messageOf } from '~/utils/api-errors'
import { EM_DASH, formatNumber, formatPrice, formatUtcShort } from '~/utils/format'

type Status = 'idle' | 'pending' | 'success' | 'error'

const props = defineProps<{
  symbol: string
  tf: Timeframe
  klines: readonly Kline[]
  features: readonly FeatureRow[]
  klinesStatus: Status
  klinesError: unknown
  featuresStatus: Status
  featuresError: unknown
  prefs: IndicatorPrefs
  hollowUp: boolean
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

/** Mantém o gráfico anterior visível e esmaecido durante a troca (sem flash). */
const view = computed<'loading' | 'empty' | 'error' | 'ready'>(() => {
  if (props.klinesStatus === 'error' && !hasData.value) return 'error'
  if (hasData.value) return 'ready'
  if (props.klinesStatus === 'pending' || props.klinesStatus === 'idle') return 'loading'
  return 'empty'
})
const refreshing = computed(() => props.klinesStatus === 'pending' && hasData.value)

const meta = computed(() => TIMEFRAME_META[props.tf])
const canLoadOlder = computed(() => props.tf === '1d' && props.klines.length >= LIMIT_BY_TF['1d'])
const countLabel = computed(() => {
  const n = props.klines.length
  return `${formatNumber(n, 0)} velas · ${meta.value.retention}`
})
const altTf = computed<Timeframe>(() => (props.tf === '1d' ? '1h' : '1d'))
const panes = computed(() => 1 + (props.prefs.rsi ? 1 : 0) + (props.prefs.macd ? 1 : 0))

// ---- Tabela alternativa (acessibilidade / conferência) ----
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
  <UCard
    class="flex h-full min-h-[520px] flex-col overflow-hidden rounded-lg"
    :ui="{ root: 'flex flex-col', body: 'relative flex-1 p-0 sm:p-0 min-h-0', footer: 'px-3 py-2 sm:px-3' }"
  >
    <div class="relative h-full min-h-[440px]">
      <!-- Alerta de dados velhos (o gráfico continua utilizável) -->
      <UAlert
        v-if="props.stale && view === 'ready'"
        class="absolute inset-x-3 top-3 z-10 border border-(--cf-warning)/40 bg-warn text-warn"
        icon="i-lucide-triangle-alert"
        color="neutral"
        variant="subtle"
        :ui="{ root: 'py-2', title: 'text-[13px]', description: 'text-[12px]' }"
        title="Dados mais antigos que o esperado."
        :description="`Os candles deveriam ter sido atualizados há ~${props.hoursLate} h (00:05 UTC). O gráfico continua utilizável; os valores podem não refletir o último dia.`"
        :actions="[{ label: 'Tentar novamente', variant: 'link', color: 'neutral', class: 'text-warn underline', onClick: () => emit('retry') }]"
      />

      <!-- Indicadores falharam (candles seguem) -->
      <div
        v-if="view === 'ready' && props.featuresStatus === 'error'"
        class="absolute right-3 top-3 z-10 rounded-md border border-default bg-elevated/95 px-2.5 py-1.5 text-[12px] text-muted"
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
      </div>

      <ChartSkeleton
        v-if="view === 'loading'"
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
        class="h-full transition-opacity"
        :class="refreshing ? 'opacity-60' : ''"
        :aria-busy="refreshing"
      >
        <ClientOnly>
          <ChartCandlestickChart
            :symbol="props.symbol"
            :tf="props.tf"
            :klines="props.klines"
            :features="props.features"
            :prefs="props.prefs"
            :hollow-up="props.hollowUp"
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
          class="absolute left-3 top-1/2 z-10 -translate-y-1/2"
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

    <template #footer>
      <div class="num flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-[11px] text-dimmed">
        <span>Eixo em UTC · arraste para navegar · scroll para zoom · ┆ linha de corte = último dado observado</span>
        <span class="flex items-center gap-3">
          <span>{{ countLabel }}</span>
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
        </span>
      </div>
    </template>
  </UCard>
</template>
