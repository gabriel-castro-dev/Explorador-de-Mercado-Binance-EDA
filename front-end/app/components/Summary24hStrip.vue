<script setup lang="ts">
import type { Ticker24h } from '~/types/api'
import type { FreshnessState } from '~/composables/useFreshness'
import type { AsyncStatus } from '~/utils/async-state'
import { baseAsset } from '~/utils/constants'
import { spreadPercent } from '~/utils/tickers'
import { EM_DASH, arrowOf, formatChange, formatCompact, formatNumber, formatPercent, formatPrice, toneOf } from '~/utils/format'

/**
 * Resumo 24h abaixo do gráfico (Design.md §10): faixa aberta com divisores
 * verticais. Nada de stat tiles encaixotados — só hairlines e macroespaço.
 */
const props = defineProps<{
  symbol: string
  ticker: Ticker24h | null
  status: AsyncStatus
  freshness: { state: FreshnessState, atUtc: string, ago: string }
}>()
const emit = defineEmits<{ (e: 'retry'): void }>()

interface Cell { label: string, value: string, sub?: string, tone?: 'up' | 'down' | 'flat' | null }

const loading = computed(() => props.status === 'pending' && !props.ticker)

const cells = computed<Cell[]>(() => {
  const t = props.ticker
  if (!t) return []
  const pct = t.price_change_percent
  const spread = spreadPercent(t)
  return [
    { label: 'Último preço', value: formatPrice(t.last_price), sub: t.last_price == null ? 'sem snapshot' : 'USDT' },
    {
      label: 'Variação 24h',
      value: t.price_change == null && pct == null
        ? EM_DASH
        : `${arrowOf(pct)} ${formatChange(t.price_change, t.last_price)} · ${formatPercent(pct)}`.trim(),
      tone: toneOf(pct),
    },
    { label: 'Abertura', value: formatPrice(t.open_price), sub: t.open_price == null ? 'sem snapshot' : 'USDT' },
    { label: 'Máx / Mín', value: `${formatPrice(t.high_price)} · ${formatPrice(t.low_price)}` },
    { label: 'Preço médio pond.', value: formatPrice(t.weighted_avg_price), sub: t.weighted_avg_price == null ? 'sem snapshot' : 'USDT' },
    { label: 'Bid / Ask', value: `${formatPrice(t.bid_price)} / ${formatPrice(t.ask_price)}`, sub: spread === null ? undefined : `spread ${formatNumber(spread, 3)} %` },
    { label: 'Volume 24h', value: t.volume == null ? EM_DASH : `${formatCompact(t.volume)} ${baseAsset(t.symbol)}`, sub: `${formatCompact(t.quote_volume)} USDT` },
    { label: 'Trades', value: formatCompact(t.count) },
  ]
})

function toneClass(tone: Cell['tone']) {
  return tone === 'up' ? 'text-up' : tone === 'down' ? 'text-down' : tone === 'flat' ? 'text-flat' : 'text-hi'
}
</script>

<template>
  <section aria-labelledby="resumo24h-titulo">
    <div class="cf-hairline-b flex flex-wrap items-baseline justify-between gap-x-5 gap-y-2 pb-3">
      <h2
        id="resumo24h-titulo"
        class="eyebrow text-muted"
      >
        Resumo 24h · <span translate="no">{{ props.symbol }}</span>
      </h2>
      <span
        class="num text-[11px]"
        :class="props.freshness.state === 'stale' ? 'text-warn' : 'text-dimmed'"
      >
        <template v-if="props.freshness.state === 'loading'"><USkeleton class="inline-block h-3 w-44 align-middle" /></template>
        <template v-else-if="props.freshness.state === 'stale'">snapshot {{ props.freshness.atUtc }} · {{ props.freshness.ago }} · esperado ≤ 2 h</template>
        <template v-else-if="props.ticker">snapshot {{ props.freshness.atUtc }} · {{ props.freshness.ago }} · atualiza de hora em hora</template>
      </span>
    </div>

    <div
      v-if="loading"
      role="status"
      aria-busy="true"
    >
      <span class="sr-only">Carregando o resumo 24h…</span>
      <div class="cf-strip grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8">
        <div
          v-for="i in 8"
          :key="i"
          class="space-y-2.5 py-4"
        >
          <USkeleton class="h-2.5 w-20" />
          <USkeleton class="h-4 w-24" />
        </div>
      </div>
    </div>

    <div
      v-else-if="props.status === 'error' && !props.ticker"
      class="flex flex-wrap items-center gap-x-3 gap-y-1 py-4 text-[14px] text-muted"
      role="alert"
    >
      <span>Resumo 24h indisponível.</span>
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
      class="py-4 text-[14px] text-muted"
      role="status"
    >
      Sem resumo 24h para este ativo ainda.
    </p>

    <dl
      v-else
      class="cf-strip grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8"
    >
      <div
        v-for="cell in cells"
        :key="cell.label"
        class="min-w-0 py-4"
      >
        <dt class="eyebrow text-dimmed">
          {{ cell.label }}
        </dt>
        <dd
          class="num mt-2 truncate text-[15px]"
          :class="toneClass(cell.tone)"
          :title="cell.value"
        >
          {{ cell.value }}
        </dd>
        <dd
          v-if="cell.sub"
          class="num mt-1 truncate text-[11px] text-dimmed"
        >
          {{ cell.sub }}
        </dd>
      </div>
    </dl>
  </section>
</template>

<style scoped>
/*
 * Divisores verticais da faixa (Design.md §10): hairline entre colunas, nunca
 * ao redor. O primeiro item de cada linha da grade perde a régua e o recuo —
 * por isso o corte muda junto com o número de colunas.
 */
.cf-strip > * {
  padding-inline: 16px;
  border-inline-start: 1px solid var(--cf-hairline-soft);
}

.cf-strip > :nth-child(2n + 1) {
  padding-inline-start: 0;
  border-inline-start: 0;
}

@media (min-width: 768px) {
  .cf-strip > :nth-child(2n + 1) {
    padding-inline-start: 16px;
    border-inline-start: 1px solid var(--cf-hairline-soft);
  }

  .cf-strip > :nth-child(4n + 1) {
    padding-inline-start: 0;
    border-inline-start: 0;
  }
}

@media (min-width: 1280px) {
  .cf-strip > :nth-child(4n + 1) {
    padding-inline-start: 16px;
    border-inline-start: 1px solid var(--cf-hairline-soft);
  }

  .cf-strip > :nth-child(8n + 1) {
    padding-inline-start: 0;
    border-inline-start: 0;
  }
}
</style>
