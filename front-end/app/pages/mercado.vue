<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import { symbolName } from '~/utils/constants'
import { filterTickers, latestSnapshotAt } from '~/utils/tickers'
import { describeError, messageOf } from '~/utils/api-errors'

useHead({ title: 'Mercado · crypto forecasting' })

const { symbol, tf } = useDashboardQuery()
const tickers = useTickers24h()
const query = ref('')
const isMobile = useMediaQuery('(max-width: 767px)')

const rows = computed(() => filterTickers(tickers.data.value, query.value, symbolName))
const snapshotAt = computed(() => latestSnapshotAt(tickers.data.value))
const fresh = useFreshness('tickers', snapshotAt, () => tickers.status.value)

const refreshing = ref(false)
async function refresh() {
  refreshing.value = true
  try {
    await tickers.refresh()
  } finally {
    refreshing.value = false
  }
}

function openSymbol(s: string) {
  return navigateTo({ path: '/', query: { symbol: s, tf: tf.value } })
}

const errorDetail = computed(() => describeError(tickers.error.value))
const errorMessage = computed(() => messageOf(tickers.error.value))
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-[20px] font-semibold text-highlighted">
          Mercado · resumo 24h
        </h1>
        <p class="mt-0.5 text-[13px] text-muted">
          Top 20 pares USDT por volume. Clique em um ativo para abri-lo no dashboard.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <UInput
          v-model="query"
          type="search"
          icon="i-lucide-search"
          placeholder="Filtrar ativo…"
          aria-label="Filtrar ativo"
          class="w-full sm:w-[220px]"
        />
        <SnapshotBadge
          :state="fresh.state.value"
          :label="fresh.label.value"
        />
        <UButton
          color="neutral"
          variant="outline"
          icon="i-lucide-refresh-cw"
          :loading="refreshing"
          :label="refreshing ? 'Atualizando…' : 'Atualizar'"
          @click="refresh"
        />
      </div>
    </div>

    <UCard
      v-if="tickers.status.value === 'error' && !tickers.data.value.length"
      class="rounded-lg"
    >
      <ErrorState
        title="Não foi possível carregar o mercado"
        :description="errorMessage"
        :detail="errorDetail"
        :retrying="refreshing"
        @retry="refresh"
      />
    </UCard>

    <UCard
      v-else-if="tickers.status.value === 'success' && !tickers.data.value.length"
      class="rounded-lg"
    >
      <EmptyState
        title="Nenhum snapshot disponível"
        description="Tente novamente em alguns minutos."
        icon="i-lucide-table-2"
        :actions="[{ label: 'Tentar novamente', color: 'neutral', variant: 'outline', onClick: refresh }]"
      />
    </UCard>

    <MarketListMobile
      v-else-if="isMobile"
      :rows="rows"
      :selected-symbol="symbol"
      :loading="tickers.status.value === 'pending'"
      :tf="tf"
    />

    <UCard
      v-else
      class="rounded-lg"
      :ui="{ body: 'p-0 sm:p-0', footer: 'px-3 py-2 sm:px-3' }"
    >
      <Tickers24hTable
        :rows="rows"
        :selected-symbol="symbol"
        :loading="tickers.status.value === 'pending'"
        @select="openSymbol"
      />
      <template #footer>
        <div class="num flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-[11px] text-dimmed">
          <span>{{ rows.length }} ativos · ordenado por volume (USDT) desc · cabeçalhos ordenáveis (Enter/Espaço)</span>
          <span>▲ alta · ▼ baixa · sem seta = sem variação · — = sem dados</span>
        </div>
      </template>
    </UCard>
  </div>
</template>
