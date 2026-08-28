<script setup lang="ts">
import { HORIZONS, type HorizonSummary } from '~/types/forecast'
import { formatNumber, formatUtc } from '~/utils/format'

/**
 * Previsões (Design.md §11): resumo da rodada, horizontes, tabela de cenários e
 * Monte Carlo. A rodada vem de `GET /api/v1/forecasts`; o Monte Carlo segue no
 * estado honesto até a API expor trajetórias — nenhum número é inventado.
 */
useHead({ title: 'Previsões · CRYPTO FORECASTING' })

const forecasts = useForecasts()

// Ativo da nuvem: `?symbol=` na URL (compartilhável); sem ele, o primeiro da rodada.
const { symbol: querySymbol } = useDashboardQuery()
const symbolOptions = computed(() => forecasts.rows.value.map(r => r.symbol))
const mcSymbol = computed<string | null>({
  get: () => querySymbol.value ?? symbolOptions.value[0] ?? null,
  set: (value) => {
    querySymbol.value = value
  },
})
// USelectMenu não aceita null no v-model; a página trabalha com string | null.
const mcSymbolModel = computed<string | undefined>({
  get: () => mcSymbol.value ?? undefined,
  set: (value) => {
    mcSymbol.value = value ?? null
  },
})
const monteCarlo = useMonteCarlo(mcSymbol)

/** Vazio honesto com motivo certo: sem rodada ≠ sem simulação para este ativo. */
const monteCarloEmpty = computed(() => {
  if (!forecasts.round.value) return undefined
  if (monteCarlo.status.value === 'error') return 'Não foi possível carregar a simulação deste ativo.'
  if (mcSymbol.value && monteCarlo.notFound.value) return `Sem simulação para ${mcSymbol.value} nesta rodada.`
  return undefined
})

const refreshing = ref(false)
async function refresh() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    await Promise.all([forecasts.refresh(), monteCarlo.refresh()])
  } finally {
    refreshing.value = false
  }
}

/** Sem rodada publicada, os quatro horizontes existem como estrutura com `—`. */
const horizons = computed<HorizonSummary[]>(() => {
  const published = forecasts.round.value?.horizons
  if (published?.length) return [...published]
  return HORIZONS.map(h => ({ key: h.key, changePercent: null }))
})

const roundSubtitle = computed(() => {
  const round = forecasts.round.value
  if (!round) return 'Top 20 ativos · nenhuma rodada publicada'
  return `Top 20 ativos · rodada de ${formatUtc(round.generatedAt)}`
})

const DISCLAIMER = 'Leia as previsões como cenários, não como recomendação de compra ou venda.'
</script>

<template>
  <div class="cf-gutter cf-shell pt-10 pb-16 md:pt-12 md:pb-24">
    <!-- Cabeçalho + faixa de versão/MAE/direção -->
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="cf-h1 uppercase">
          Previsões do modelo
        </h1>
        <p class="num mt-2.5 text-[13px] text-muted">
          {{ roundSubtitle }}
        </p>
      </div>
      <ForecastRoundFacts :round="forecasts.round.value" />
    </div>

    <!-- Resumo da rodada + horizontes (Design.md §11.1) -->
    <section
      class="cf-section grid gap-14 lg:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)] lg:items-center lg:gap-12 xl:gap-16"
      aria-label="Resumo da rodada e horizontes"
    >
      <ForecastRoundSummary :round="forecasts.round.value" />
      <div v-reveal="{ y: 28, delay: 120 }">
        <ForecastHorizonArcs :horizons="horizons" />
      </div>
    </section>

    <p class="cf-hairline-t flex items-start gap-3 pt-5 text-[14px] text-muted">
      <UIcon
        name="i-lucide-info"
        class="mt-0.5 size-4 shrink-0 text-dimmed"
        aria-hidden="true"
      />
      <span>{{ DISCLAIMER }}</span>
    </p>

    <!-- Tabela de cenários (Design.md §11.2) -->
    <section class="cf-section">
      <ForecastScenarioTable
        v-reveal="{ y: 28 }"
        :rows="forecasts.rows.value"
        :refreshing="refreshing"
        @refresh="refresh"
      />
    </section>

    <!-- Monte Carlo (Design.md §11.3) -->
    <section
      class="cf-section-tight"
      aria-labelledby="monte-carlo-titulo"
    >
      <div
        v-reveal="{ y: 24 }"
        class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div>
          <h2
            id="monte-carlo-titulo"
            class="cf-h2 uppercase"
          >
            Simulação Monte Carlo
          </h2>
          <p class="num mt-2 text-[13px] text-muted">
            <template v-if="monteCarlo.series.value">
              {{ formatNumber(monteCarlo.series.value.simulatedCount, 0) }} trajetórias ·
              <span translate="no">{{ monteCarlo.series.value.symbol }}</span> ·
              horizonte de {{ monteCarlo.series.value.horizonDays }} dias
            </template>
            <template v-else>
              trajetórias simuladas a partir do último dado observado
            </template>
          </p>
        </div>

        <!-- Controles só existem quando há o que controlar -->
        <div
          v-if="symbolOptions.length"
          class="flex flex-wrap items-center gap-3"
        >
          <USelectMenu
            v-model="mcSymbolModel"
            :items="symbolOptions"
            :search-input="{ placeholder: 'Buscar ativo…', icon: 'i-lucide-search' }"
            icon="i-lucide-search"
            aria-label="Ativo da simulação"
            class="w-[180px]"
          />
          <UButton
            v-if="monteCarlo.series.value"
            color="neutral"
            variant="outline"
            icon="i-lucide-refresh-cw"
            label="Reiniciar simulação"
            @click="monteCarlo.restart()"
          />
        </div>
      </div>

      <div class="mt-8">
        <ClientOnly>
          <ForecastMonteCarloChart
            :series="monteCarlo.series.value"
            :restart-token="monteCarlo.restartToken.value"
            :empty-message="monteCarloEmpty"
          />
          <template #fallback>
            <div
              class="h-[380px] md:h-[460px] xl:h-[520px]"
              aria-hidden="true"
            />
          </template>
        </ClientOnly>
      </div>
    </section>

    <p class="cf-hairline-t pt-5 text-[13px] text-dimmed">
      {{ DISCLAIMER }}
    </p>
  </div>
</template>
