<script setup lang="ts">
import type { Ticker24h } from '~/types/api'
import { symbolName } from '~/utils/constants'
import { sortTickers, tickerHasData, type SortDir, type TickerSortKey } from '~/utils/tickers'
import { EM_DASH, arrowOf, formatChange, formatCompact, formatPercent, formatPrice, toneOf } from '~/utils/format'

const props = defineProps<{
  rows: readonly Ticker24h[]
  selectedSymbol: string | null
  loading: boolean
}>()
const emit = defineEmits<{ (e: 'select', symbol: string): void }>()

interface Col { key: TickerSortKey, label: string, align?: 'left' | 'right', fmt: (t: Ticker24h) => string, tone?: (t: Ticker24h) => 'up' | 'down' | 'flat' | null, sticky?: boolean }

const COLUMNS: Col[] = [
  { key: 'symbol', label: 'Ativo', align: 'left', fmt: t => t.symbol, sticky: true },
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
    <table class="w-full min-w-[1080px] border-collapse text-[13px]">
      <thead>
        <tr class="border-b border-default">
          <th
            v-for="col in COLUMNS"
            :key="col.key"
            scope="col"
            :aria-sort="ariaSort(col.key)"
            class="eyebrow whitespace-nowrap px-3 py-2.5 text-dimmed"
            :class="[col.align === 'left' ? 'text-left' : 'text-right', col.sticky ? 'sticky left-0 z-10 bg-elevated' : '']"
          >
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-sm hover:text-default"
              :class="sortKey === col.key ? 'text-highlighted' : ''"
              @click="toggleSort(col.key)"
            >
              {{ col.label }}
              <UIcon
                v-if="sortKey === col.key"
                :name="sortDir === 'desc' ? 'i-lucide-chevron-down' : 'i-lucide-chevron-up'"
                class="size-3"
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
            class="border-b border-muted"
          >
            <td
              v-for="col in COLUMNS"
              :key="col.key"
              class="px-3 py-2.5"
            >
              <USkeleton class="ml-auto h-3 w-16" />
            </td>
          </tr>
        </template>
        <tr
          v-for="t in sorted"
          v-else
          :key="t.symbol"
          tabindex="0"
          class="cursor-pointer border-b border-muted outline-none hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-primary"
          :class="t.symbol === props.selectedSymbol ? 'bg-primary-soft' : ''"
          :aria-selected="t.symbol === props.selectedSymbol"
          @click="emit('select', t.symbol)"
          @keydown.enter.prevent="emit('select', t.symbol)"
          @keydown.space.prevent="emit('select', t.symbol)"
        >
          <td
            v-for="col in COLUMNS"
            :key="col.key"
            class="whitespace-nowrap px-3 py-2.5"
            :class="[
              col.align === 'left' ? 'text-left' : 'num text-right',
              col.sticky ? 'sticky left-0 z-10 bg-elevated' : '',
              col.tone ? toneClass(col.tone(t)) : '',
              !tickerHasData(t) && col.key !== 'symbol' ? 'text-dimmed' : '',
            ]"
            :title="!tickerHasData(t) && col.key !== 'symbol' ? 'Sem snapshot recente para este ativo' : undefined"
          >
            <template v-if="col.key === 'symbol'">
              <span
                class="num font-medium text-highlighted"
                translate="no"
              >{{ t.symbol }}</span>
              <span
                v-if="!tickerHasData(t)"
                class="num ml-2 text-[11px] text-dimmed"
              >sem dados</span>
              <span
                v-else-if="symbolName(t.symbol)"
                class="sr-only"
              >{{ symbolName(t.symbol) }}</span>
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
