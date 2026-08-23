<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { Ticker24h } from '~/types/api'
import { symbolName } from '~/utils/constants'
import { sortTickers, tickerHasData, type TickerSortKey } from '~/utils/tickers'
import { arrowOf, formatCompact, formatPercent, formatPrice, toneOf } from '~/utils/format'

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
    <div class="mb-2 flex items-center justify-between">
      <span class="text-[12px] text-muted">{{ props.rows.length }} ativos</span>
      <UDropdownMenu :items="menu">
        <UButton
          color="neutral"
          variant="outline"
          size="sm"
          :label="sortLabel"
          trailing-icon="i-lucide-chevron-down"
          aria-label="Ordenar por"
        />
      </UDropdownMenu>
    </div>
    <UCard
      class="rounded-lg"
      :ui="{ body: 'p-0 sm:p-0' }"
    >
      <div
        v-if="props.loading && !props.rows.length"
        class="divide-y divide-muted"
      >
        <div
          v-for="i in 8"
          :key="i"
          class="flex h-14 items-center justify-between px-4"
        >
          <USkeleton class="h-3 w-24" />
          <USkeleton class="h-3 w-20" />
        </div>
      </div>
      <ul
        v-else
        class="divide-y divide-muted"
      >
        <li
          v-for="t in sorted"
          :key="t.symbol"
        >
          <NuxtLink
            :to="{ path: '/graficos', query: { symbol: t.symbol, tf: props.tf } }"
            class="flex h-14 items-center justify-between gap-3 px-4"
            :class="t.symbol === props.selectedSymbol ? 'bg-primary-soft' : ''"
          >
            <span class="min-w-0">
              <span
                class="num block font-medium text-highlighted"
                translate="no"
              >{{ t.symbol }}</span>
              <span class="num block truncate text-[11px] text-muted">
                <template v-if="!tickerHasData(t)">sem dados</template>
                <template v-else>{{ symbolName(t.symbol) ?? '' }}{{ symbolName(t.symbol) ? ' · ' : '' }}vol {{ formatCompact(t.quote_volume) }}</template>
              </span>
            </span>
            <span class="num flex shrink-0 flex-col items-end">
              <span class="text-default">{{ formatPrice(t.last_price) }}</span>
              <span
                class="text-[12px]"
                :class="toneClass(t.price_change_percent)"
              >{{ arrowOf(t.price_change_percent) }} {{ formatPercent(t.price_change_percent) }}</span>
            </span>
          </NuxtLink>
        </li>
      </ul>
    </UCard>
    <p class="num mt-2 text-[11px] text-dimmed">
      Lista resumida no celular · a tabela completa está no desktop
    </p>
  </div>
</template>
