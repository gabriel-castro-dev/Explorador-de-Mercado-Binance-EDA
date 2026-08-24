<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import { symbolName } from '~/utils/constants'
import { filterTickers, latestSnapshotAt } from '~/utils/tickers'
import { asyncView } from '~/utils/async-state'
import { describeError, messageOf } from '~/utils/api-errors'

/**
 * Mercado (Design.md §12.1): tabela full-bleed com hairlines e wash na linha
 * ativa; nenhum card externo. Ordem padrão: volume USDT decrescente, nulls no fim.
 */
useHead({ title: 'Mercado · CRYPTO FORECASTING' })

const { symbol, tf } = useDashboardQuery()
const tickers = useTickers24h()
const query = ref('')
const isMobile = useMediaQuery('(max-width: 767px)')

const rows = computed(() => filterTickers(tickers.data.value, query.value, symbolName))
const snapshotAt = computed(() => latestSnapshotAt(tickers.data.value))
const fresh = useFreshness('tickers', snapshotAt, () => tickers.status.value)

const view = computed(() => asyncView(tickers.status.value, tickers.data.value.length > 0))

const refreshing = ref(false)
async function refresh() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    await tickers.refresh()
  } finally {
    refreshing.value = false
  }
}

const errorDetail = computed(() => describeError(tickers.error.value))
const errorMessage = computed(() => messageOf(tickers.error.value))
</script>

<template>
  <div class="cf-gutter cf-shell pt-10 pb-16 md:pt-12 md:pb-20">
    <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="cf-h1 uppercase">
          Mercado
        </h1>
        <p class="mt-2.5 text-[15px] text-muted">
          Resumo 24h dos top 20 pares USDT por volume. Abra um ativo para ver o gráfico.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-x-5 gap-y-3">
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
          aria-label="Atualizar dados"
          @click="refresh"
        />
      </div>
    </div>

    <div class="mt-10">
      <ErrorState
        v-if="view === 'error'"
        title="Não foi possível carregar o mercado"
        :description="errorMessage"
        :detail="errorDetail"
        :retrying="refreshing"
        @retry="refresh"
      />

      <EmptyState
        v-else-if="view === 'empty'"
        title="Nenhum snapshot disponível"
        description="O resumo 24h atualiza de hora em hora. Tente novamente em alguns minutos."
        icon="i-lucide-table-2"
        :actions="[{ label: 'Tentar novamente', color: 'neutral', variant: 'outline', onClick: refresh }]"
      />

      <MarketListMobile
        v-else-if="isMobile"
        :rows="rows"
        :selected-symbol="symbol"
        :loading="tickers.status.value === 'pending'"
        :tf="tf"
      />

      <Tickers24hTable
        v-else
        :rows="rows"
        :selected-symbol="symbol"
        :loading="tickers.status.value === 'pending'"
        :tf="tf"
      />
    </div>

    <p
      v-if="view === 'ready'"
      class="cf-hairline-t num mt-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-1 pt-4 text-[11px] text-dimmed"
    >
      <span>{{ rows.length }} ativos · ordenado por volume (USDT) decrescente</span>
      <span>▲ alta · ▼ baixa · +0,00 % sem variação · — sem dados</span>
    </p>
  </div>
</template>
