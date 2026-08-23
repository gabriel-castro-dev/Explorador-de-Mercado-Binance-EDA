<script setup lang="ts">
import type { Ticker24h } from '~/types/api'
import type { FreshnessState } from '~/composables/useFreshness'
import { baseAsset } from '~/utils/constants'
import { spreadPercent } from '~/utils/tickers'
import { EM_DASH, arrowOf, formatChange, formatCompact, formatNumber, formatPercent, formatPrice, toneOf } from '~/utils/format'

type Status = 'idle' | 'pending' | 'success' | 'error'

const props = defineProps<{
  symbol: string
  ticker: Ticker24h | null
  status: Status
  freshness: { state: FreshnessState, atUtc: string, ago: string }
}>()
const emit = defineEmits<{ (e: 'retry'): void }>()

interface Tile { label: string, value: string, sub?: string, tone?: 'up' | 'down' | 'flat' | 'ai' | null, dense?: boolean, chip?: string }

const loading = computed(() => props.status === 'pending' && !props.ticker)
const tiles = computed<Tile[]>(() => {
  const t = props.ticker
  if (!t) return []
  const pct = t.price_change_percent
  const tone = toneOf(pct)
  const spread = spreadPercent(t)
  return [
    { label: 'Último preço', value: formatPrice(t.last_price), sub: t.last_price == null ? 'sem snapshot' : 'USDT' },
    { label: 'Variação 24h', value: t.price_change == null && pct == null ? EM_DASH : `${arrowOf(pct)} ${formatChange(t.price_change, t.last_price)} · ${formatPercent(pct)}`.trim(), tone },
    { label: 'Abertura', value: formatPrice(t.open_price), sub: t.open_price == null ? 'sem snapshot' : 'USDT' },
    { label: 'Máx / Mín', value: `${formatPrice(t.high_price)} · ${formatPrice(t.low_price)}`, dense: true },
    { label: 'Preço médio pond.', value: formatPrice(t.weighted_avg_price), sub: t.weighted_avg_price == null ? 'sem snapshot' : 'USDT' },
    { label: 'Bid / Ask', value: `${formatPrice(t.bid_price)} / ${formatPrice(t.ask_price)}`, sub: spread === null ? undefined : `spread ${formatNumber(spread, 3)} %`, dense: true },
    { label: 'Volume 24h', value: t.volume == null ? EM_DASH : `${formatCompact(t.volume)} ${baseAsset(t.symbol)}`, sub: `${formatCompact(t.quote_volume)} USDT · ${formatCompact(t.count)} trades` },
    // Ciano = IA; sem número fabricado até o modelo publicar (marco 3).
    { label: 'Previsão diária (IA)', value: EM_DASH, tone: 'ai', chip: 'IA · v0' },
  ]
})

function toneClass(tone: Tile['tone']) {
  return tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : tone === 'flat' ? 'text-flat' : tone === 'ai' ? 'text-ai' : 'text-highlighted'
}
</script>

<template>
  <UCard
    class="rounded-lg"
    :ui="{ header: 'px-4 py-2.5 sm:px-4', body: 'p-0 sm:p-0' }"
  >
    <template #header>
      <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        <h2 class="eyebrow text-muted">
          Resumo 24h · <span translate="no">{{ props.symbol }}</span>
        </h2>
        <span
          class="num text-[11px]"
          :class="props.freshness.state === 'stale' ? 'text-warn' : 'text-dimmed'"
        >
          <template v-if="props.freshness.state === 'loading'"><USkeleton class="inline-block h-3 w-40 align-middle" /></template>
          <template v-else-if="props.freshness.state === 'stale'">snapshot {{ props.freshness.atUtc }} · {{ props.freshness.ago }} · esperado ≤ 2 h</template>
          <template v-else-if="props.ticker">snapshot {{ props.freshness.atUtc }} · {{ props.freshness.ago }} · atualiza de hora em hora</template>
        </span>
      </div>
    </template>

    <div
      v-if="loading"
      class="grid grid-cols-2 divide-x divide-y divide-default md:grid-cols-4 xl:grid-cols-8 xl:divide-y-0"
    >
      <div
        v-for="i in 8"
        :key="i"
        class="space-y-2 px-4 py-3"
      >
        <USkeleton class="h-2.5 w-16" />
        <USkeleton class="h-4 w-24" />
      </div>
    </div>

    <div
      v-else-if="props.status === 'error' && !props.ticker"
      class="flex items-center justify-between gap-3 px-4 py-3 text-[13px] text-muted"
      role="alert"
    >
      Resumo 24h indisponível.
      <UButton
        variant="link"
        size="xs"
        label="Tentar novamente"
        class="p-0"
        @click="emit('retry')"
      />
    </div>

    <p
      v-else-if="!props.ticker"
      class="px-4 py-3 text-[13px] text-muted"
      role="status"
    >
      Sem resumo 24h para este ativo ainda.
    </p>

    <dl
      v-else
      class="grid grid-cols-2 divide-x divide-y divide-default md:grid-cols-4 xl:grid-cols-8 xl:divide-y-0"
    >
      <div
        v-for="tile in tiles"
        :key="tile.label"
        class="min-w-0 px-4 py-3"
      >
        <dt class="text-[11px] text-muted">
          {{ tile.label }}
        </dt>
        <dd
          class="num mt-0.5 truncate font-medium"
          :class="[toneClass(tile.tone), tile.dense ? 'text-[13px]' : 'text-[14px]']"
          :title="tile.value"
        >
          {{ tile.value }}
        </dd>
        <dd
          v-if="tile.sub"
          class="num text-[11px] text-dimmed"
        >
          {{ tile.sub }}
        </dd>
        <dd
          v-if="tile.chip"
          class="mt-1"
        >
          <span class="ai-chip text-[10px]">{{ tile.chip }}</span>
        </dd>
      </div>
    </dl>

    <template
      v-if="props.ticker || props.status !== 'pending'"
      #footer
    >
      <NuxtLink
        to="/mercado"
        class="inline-flex items-center gap-1 text-[12px] text-primary"
      >
        Ver todos os ativos <UIcon
          name="i-lucide-arrow-right"
          class="size-3.5"
        />
      </NuxtLink>
    </template>
  </UCard>
</template>
