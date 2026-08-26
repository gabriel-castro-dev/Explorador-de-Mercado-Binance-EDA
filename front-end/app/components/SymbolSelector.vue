<script setup lang="ts">
import type { SymbolRow, Ticker24h } from '~/types/api'
import { symbolName } from '~/utils/constants'
import { trackedSymbols } from '~/utils/tickers'
import { arrowOf, formatPercent, formatPrice, toneOf } from '~/utils/format'

type Status = 'idle' | 'pending' | 'success' | 'error'

const props = defineProps<{
  symbols: readonly SymbolRow[]
  tickers: readonly Ticker24h[]
  status: Status
}>()
const emit = defineEmits<{ (e: 'retry'): void }>()
const model = defineModel<string | null>({ default: null })

interface Item { symbol: string, label: string, name: string | undefined, last: number | null, pct: number | null }

const tickerBySymbol = computed(() => new Map(props.tickers.map(t => [t.symbol, t])))
// Só o universo com candles entra na lista (Design.md §10: sem dado, sem opção).
const items = computed<Item[]>(() => trackedSymbols(props.symbols).map((s) => {
  const t = tickerBySymbol.value.get(s.symbol)
  return { symbol: s.symbol, label: s.symbol, name: symbolName(s.symbol), last: t?.last_price ?? null, pct: t?.price_change_percent ?? null }
}))

const selected = computed<Item | undefined>({
  get: () => items.value.find(i => i.symbol === model.value),
  set: (v) => {
    if (v) model.value = v.symbol
  },
})

const loading = computed(() => props.status === 'pending' && props.symbols.length === 0)
const failed = computed(() => props.status === 'error' && props.symbols.length === 0)

function toneClass(pct: number | null) {
  const tone = toneOf(pct)
  return tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : 'text-flat'
}
</script>

<template>
  <div class="flex items-center gap-2">
    <USelectMenu
      v-if="!failed"
      v-model="selected"
      :items="items"
      :loading="loading"
      :disabled="loading"
      :filter-fields="['symbol', 'name']"
      :search-input="{ placeholder: 'Buscar ativo…', icon: 'i-lucide-search', autofocus: true }"
      icon="i-lucide-search"
      size="lg"
      aria-label="Ativo"
      class="w-[220px] sm:w-[240px]"
      :ui="{ content: 'w-[320px] max-h-[360px]', item: 'py-1.5' }"
    >
      <template #default="{ modelValue }">
        <span
          v-if="modelValue"
          class="flex items-center gap-2 truncate"
        >
          <span
            class="num text-[15px] text-hi"
            translate="no"
          >{{ modelValue.symbol }}</span>
          <span
            v-if="modelValue.name"
            class="truncate text-[13px] text-muted"
          >{{ modelValue.name }}</span>
        </span>
        <span
          v-else-if="loading"
          class="flex items-center gap-2"
        ><USkeleton class="h-3 w-28" /></span>
        <span
          v-else
          class="text-dimmed"
        >Escolher ativo</span>
      </template>

      <template #item="{ item }">
        <span class="flex w-full items-center justify-between gap-3">
          <span class="flex min-w-0 flex-col">
            <span
              class="num text-[15px] text-hi"
              translate="no"
            >{{ item.symbol }}</span>
            <span
              v-if="item.name"
              class="truncate text-[11px] text-muted"
            >{{ item.name }}</span>
          </span>
          <span class="num flex shrink-0 flex-col items-end text-[12px]">
            <span class="text-default">{{ formatPrice(item.last) }}</span>
            <span :class="toneClass(item.pct)">{{ arrowOf(item.pct) }} {{ formatPercent(item.pct) }}</span>
          </span>
        </span>
      </template>

      <template #empty>
        <span class="text-[12px]">Nenhum ativo encontrado</span>
      </template>

      <template #content-bottom>
        <div class="num flex items-center justify-between border-t border-default px-3 py-1.5 text-[11px] text-dimmed">
          <span>{{ items.length }} ativos rastreados · candles diários</span>
          <span>↑↓ · Enter</span>
        </div>
      </template>
    </USelectMenu>

    <UTooltip
      v-else
      text="Não foi possível carregar os ativos. Tentar novamente"
    >
      <UButton
        color="neutral"
        variant="outline"
        icon="i-lucide-triangle-alert"
        label="Ativos indisponíveis"
        class="text-warn"
        aria-label="Não foi possível carregar os ativos. Tentar novamente"
        @click="emit('retry')"
      />
    </UTooltip>
  </div>
</template>
