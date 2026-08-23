<script setup lang="ts">
import type { Ticker24h } from '~/types/api'
import { symbolName } from '~/utils/constants'
import { sortTickers, tickerHasData, type SortDir, type TickerSortKey } from '~/utils/tickers'
import { EM_DASH, arrowOf, formatChange, formatCompact, formatPercent, formatPrice, toneOf } from '~/utils/format'

/**
 * Mercado — resumo 24h (Design.md §12.1): mesma linguagem da tabela de cenários.
 * Full-bleed, hairlines, wash horizontal na linha ativa; nenhum card externo.
 * Nulls sempre por último, independente da direção da ordenação.
 */
const props = defineProps<{
  rows: readonly Ticker24h[]
  selectedSymbol: string | null
  loading: boolean
  /** Timeframe vigente — os links para /graficos preservam o estado compartilhado. */
  tf: string
}>()

interface Col {
  key: TickerSortKey
  label: string
  align?: 'start' | 'end'
  fmt: (t: Ticker24h) => string
  tone?: (t: Ticker24h) => 'up' | 'down' | 'flat' | null
}

const COLUMNS: Col[] = [
  { key: 'symbol', label: 'Ativo', align: 'start', fmt: t => t.symbol },
  { key: 'last_price', label: 'Último', fmt: t => formatPrice(t.last_price) },
  { key: 'price_change', label: 'Var. 24h', fmt: t => formatChange(t.price_change, t.last_price), tone: t => toneOf(t.price_change) },
  { key: 'price_change_percent', label: 'Var. %', fmt: t => (t.price_change_percent == null ? EM_DASH : `${arrowOf(t.price_change_percent)} ${formatPercent(t.price_change_percent)}`.trim()), tone: t => toneOf(t.price_change_percent) },
  { key: 'weighted_avg_price', label: 'Preço médio', fmt: t => formatPrice(t.weighted_avg_price) },
  { key: 'open_price', label: 'Abertura', fmt: t => formatPrice(t.open_price) },
  { key: 'high_price', label: 'Máxima', fmt: t => formatPrice(t.high_price) },
  { key: 'low_price', label: 'Mínima', fmt: t => formatPrice(t.low_price) },
  { key: 'bid_price', label: 'Bid', fmt: t => formatPrice(t.bid_price) },
  { key: 'ask_price', label: 'Ask', fmt: t => formatPrice(t.ask_price) },
  { key: 'volume', label: 'Volume (base)', fmt: t => formatCompact(t.volume) },
  { key: 'quote_volume', label: 'Volume (USDT)', fmt: t => formatCompact(t.quote_volume) },
  { key: 'count', label: 'Trades', fmt: t => formatCompact(t.count) },
]

const sortKey = ref<TickerSortKey>('quote_volume')
const sortDir = ref<SortDir>('desc')
const sorted = computed(() => sortTickers(props.rows, sortKey.value, sortDir.value))

function toggleSort(key: TickerSortKey) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  else {
    sortKey.value = key
    sortDir.value = key === 'symbol' ? 'asc' : 'desc'
  }
}

function ariaSort(key: TickerSortKey): 'ascending' | 'descending' | 'none' {
  if (sortKey.value !== key) return 'none'
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

function toneClass(tone: 'up' | 'down' | 'flat' | null) {
  return tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : tone === 'flat' ? 'text-flat' : ''
}

defineExpose({ sortKey, sortDir })
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full min-w-[1040px] border-collapse text-[13.5px]">
      <caption class="sr-only">
        Resumo 24h por ativo. Cabeçalhos ordenáveis; dados ausentes aparecem como travessão e vão para o fim da lista.
      </caption>
      <thead>
        <tr class="cf-hairline-b">
          <th
            v-for="col in COLUMNS"
            :key="col.key"
            scope="col"
            :aria-sort="ariaSort(col.key)"
            class="py-3 pe-4 whitespace-nowrap"
            :class="col.align === 'start' ? 'text-start' : 'text-end'"
          >
            <button
              type="button"
              class="eyebrow inline-flex min-h-9 items-center gap-1.5 rounded-sm"
              :class="sortKey === col.key ? 'text-hi' : 'text-dimmed hover:text-muted'"
              @click="toggleSort(col.key)"
            >
              {{ col.label }}
              <UIcon
                v-if="sortKey === col.key"
                :name="sortDir === 'desc' ? 'i-lucide-arrow-down' : 'i-lucide-arrow-up'"
                class="size-3"
                aria-hidden="true"
              />
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        <template v-if="props.loading && !props.rows.length">
          <tr
            v-for="i in 8"
            :key="i"
            class="cf-rule"
          >
            <td
              v-for="col in COLUMNS"
              :key="col.key"
              class="py-3.5 pe-4"
            >
              <USkeleton class="h-3 w-16" />
            </td>
          </tr>
        </template>
        <tr
          v-for="t in sorted"
          v-else
          :key="t.symbol"
          class="cf-rule transition-colors hover:cf-row-hover focus-within:cf-row-hover"
          :class="t.symbol === props.selectedSymbol ? 'cf-row-hover' : ''"
        >
          <td
            v-for="col in COLUMNS"
            :key="col.key"
            class="py-3.5 pe-4 whitespace-nowrap"
            :class="[
              col.align === 'start' ? 'text-start' : 'num text-end',
              col.tone ? toneClass(col.tone(t)) : '',
              !tickerHasData(t) && col.key !== 'symbol' ? 'text-dimmed' : '',
            ]"
            :title="!tickerHasData(t) && col.key !== 'symbol' ? 'Sem snapshot recente para este ativo' : undefined"
          >
            <template v-if="col.key === 'symbol'">
              <NuxtLink
                :to="{ path: '/graficos', query: { symbol: t.symbol, tf: props.tf } }"
                class="num rounded-sm text-[15px] text-hi"
                translate="no"
              >
                {{ t.symbol }}
                <span class="sr-only">— abrir {{ symbolName(t.symbol) ?? t.symbol }} nos gráficos</span>
              </NuxtLink>
              <span
                v-if="!tickerHasData(t)"
                class="num ms-2 text-[11px] text-dimmed"
              >sem dados</span>
            </template>
            <template v-else>
              {{ col.fmt(t) }}
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
