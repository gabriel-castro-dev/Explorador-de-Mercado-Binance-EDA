<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { Ticker24h } from '~/types/api'
import { symbolName } from '~/utils/constants'
import { sortTickers, tickerHasData, type TickerSortKey } from '~/utils/tickers'
import { arrowOf, formatCompact, formatPercent, formatPrice, toneOf } from '~/utils/format'

/**
 * Mercado no mobile (Design.md §12.1): linhas de 56 px, símbolo e nome à
 * esquerda, último preço e variação à direita. Lista aberta, sem card.
 */
const props = defineProps<{
  rows: readonly Ticker24h[]
  selectedSymbol: string | null
  loading: boolean
  tf: string
}>()

const SORTS: { key: TickerSortKey, label: string }[] = [
  { key: 'quote_volume', label: 'Volume' },
  { key: 'price_change_percent', label: 'Var. %' },
  { key: 'last_price', label: 'Último' },
  { key: 'symbol', label: 'Ativo' },
]
const sortKey = ref<TickerSortKey>('quote_volume')
const sortLabel = computed(() => SORTS.find(s => s.key === sortKey.value)?.label ?? 'Volume')
const sorted = computed(() => sortTickers(props.rows, sortKey.value, sortKey.value === 'symbol' ? 'asc' : 'desc'))
const menu = computed<DropdownMenuItem[]>(() => SORTS.map(s => ({
  label: s.label,
  icon: sortKey.value === s.key ? 'i-lucide-check' : undefined,
  onSelect: () => {
    sortKey.value = s.key
  },
})))

function toneClass(v: number | null | undefined) {
  const tone = toneOf(v)
  return tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : 'text-flat'
}
</script>

<template>
  <div>
    <div class="cf-hairline-b flex items-center justify-between gap-3 pb-3">
      <span class="num text-[12px] text-dimmed">{{ props.rows.length }} ativos</span>
      <UDropdownMenu :items="menu">
        <UButton
          color="neutral"
          variant="ghost"
          size="sm"
          :label="`Ordenar: ${sortLabel}`"
          trailing-icon="i-lucide-chevron-down"
        />
      </UDropdownMenu>
    </div>

    <div
      v-if="props.loading && !props.rows.length"
      role="status"
      aria-busy="true"
    >
      <span class="sr-only">Carregando o mercado…</span>
      <div
        v-for="i in 8"
        :key="i"
        class="cf-rule flex h-14 items-center justify-between"
      >
        <USkeleton class="h-3 w-28" />
        <USkeleton class="h-3 w-20" />
      </div>
    </div>

    <ul v-else>
      <li
        v-for="t in sorted"
        :key="t.symbol"
        class="cf-rule"
      >
        <NuxtLink
          :to="{ path: '/graficos', query: { symbol: t.symbol, tf: props.tf } }"
          class="flex h-14 items-center justify-between gap-3"
          :class="t.symbol === props.selectedSymbol ? 'cf-row-hover' : ''"
        >
          <span class="min-w-0">
            <span
              class="num block text-[15px] text-hi"
              translate="no"
            >{{ t.symbol }}</span>
            <span class="num block truncate text-[11px] text-muted">
              <template v-if="!tickerHasData(t)">sem dados</template>
              <template v-else>{{ symbolName(t.symbol) ?? '' }}{{ symbolName(t.symbol) ? ' · ' : '' }}vol {{ formatCompact(t.quote_volume) }}</template>
            </span>
          </span>
          <span class="num flex shrink-0 flex-col items-end">
            <span class="text-[15px] text-default">{{ formatPrice(t.last_price) }}</span>
            <span
              class="text-[12px]"
              :class="toneClass(t.price_change_percent)"
            >{{ arrowOf(t.price_change_percent) }} {{ formatPercent(t.price_change_percent) }}</span>
          </span>
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>
