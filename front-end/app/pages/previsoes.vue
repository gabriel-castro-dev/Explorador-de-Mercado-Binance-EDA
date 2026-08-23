<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { EM_DASH } from '~/utils/format'

useHead({ title: 'Previsões · crypto forecasting' })

/**
 * Estado final da tela (Design.md §5/§6): a API de forecasts chega no marco 3.
 * Até lá, chips e tabela mostram o layout real com valores vazios — nunca
 * números fabricados — e o chip "IA · v0 · em validação" marca o bloco.
 */
interface ForecastRow {
  symbol: string
  price: string
  daily: string
  weekly: string
  monthly: string
  yearly: string
  confidence: string
}

const modelChips = [
  { label: 'Versão do modelo', value: EM_DASH },
  { label: 'MAE da rodada', value: EM_DASH },
  { label: 'Acerto de direção', value: EM_DASH },
]

const columns: TableColumn<ForecastRow>[] = [
  { accessorKey: 'symbol', header: 'Ativo' },
  { accessorKey: 'price', header: 'Preço real', meta: { class: { th: 'text-right', td: 'text-right num' } } },
  { accessorKey: 'daily', header: 'Previsão diária', meta: { class: { th: 'text-right', td: 'text-right num' } } },
  { accessorKey: 'weekly', header: 'Semanal', meta: { class: { th: 'text-right', td: 'text-right num' } } },
  { accessorKey: 'monthly', header: 'Mensal', meta: { class: { th: 'text-right', td: 'text-right num' } } },
  { accessorKey: 'yearly', header: 'Anual', meta: { class: { th: 'text-right', td: 'text-right num' } } },
  { accessorKey: 'confidence', header: 'Confiança', meta: { class: { th: 'text-right', td: 'text-right num' } } },
]

const rows: ForecastRow[] = []
</script>

<template>
  <div class="space-y-4">
    <!-- Cabeçalho + chips do modelo -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[24px] font-bold tracking-[-.01em] text-highlighted">
          Previsões
        </h1>
        <p class="mt-1.5 text-[13px] text-muted">
          Horizontes diário, semanal, mensal e anual para os top 20 ativos, com a confiança do backtesting.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span
          v-for="chip in modelChips"
          :key="chip.label"
          class="num inline-flex h-8 items-center gap-2 rounded-full border border-default px-3 text-[11px] text-muted"
        >
          <span class="eyebrow">{{ chip.label }}</span>
          <span class="text-default">{{ chip.value }}</span>
        </span>
        <span class="ai-chip">IA · v0 · em validação</span>
      </div>
    </div>

    <!-- Resumo da rodada (texto de agente) — único glass-hi da tela -->
    <section
      class="glass-hi flex items-start gap-4 px-5 py-4"
      aria-label="Resumo da rodada"
    >
      <span class="mt-0.5 inline-flex size-[38px] flex-none items-center justify-center rounded-[10px] border border-[rgba(95,196,255,.35)] bg-[rgba(95,196,255,.10)] text-ai">
        <UIcon
          name="i-lucide-sparkles"
          class="size-[18px]"
        />
      </span>
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-2">
          <h2 class="font-bold text-highlighted">
            Resumo da rodada, pelo agente
          </h2>
          <span class="ai-chip text-[10px]">IA · v0 · em validação</span>
        </div>
        <p
          class="mt-1 text-[13px] text-muted"
          role="status"
        >
          O modelo ainda não publicou previsões. Quando a primeira rodada sair, este resumo cita os três maiores gaps entre preço e projeção e a média de erro por horizonte.
        </p>
        <p class="mt-2 text-[11.5px] text-dimmed">
          Leia as previsões como cenários, não como recomendação de compra ou venda.
        </p>
      </div>
    </section>

    <!-- Tabela top-20 -->
    <UCard :ui="{ body: 'p-0 sm:p-0' }">
      <template #header>
        <h2 class="eyebrow text-muted">
          Top 20 · previsões por horizonte
        </h2>
      </template>
      <UTable
        :data="rows"
        :columns="columns"
        class="text-[12.5px]"
        :ui="{ th: 'eyebrow text-dimmed py-2', td: 'py-2 whitespace-nowrap' }"
      >
        <template #empty>
          <div class="flex flex-col items-center gap-2 px-4 py-10 text-center">
            <span class="ai-chip">IA · v0 · em validação</span>
            <p class="text-[13px] text-muted">
              O modelo ainda não publicou previsões para os ativos rastreados.
            </p>
            <p class="max-w-[52ch] text-[12px] text-dimmed">
              A tabela estreia com o marco de ML: valor previsto e variação contra o preço real (gelo acima, vermelho abaixo) em cada horizonte, mais a confiança do backtesting.
            </p>
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Monte Carlo (em breve) + atalho para os cenários -->
    <div class="grid gap-4 sm:grid-cols-2">
      <section
        class="glass flex items-start gap-3 px-5 py-4 opacity-70"
        aria-label="Monte Carlo com backtesting (em breve)"
      >
        <UIcon
          name="i-lucide-dices"
          class="mt-0.5 size-5 flex-none text-dimmed"
        />
        <span class="min-w-0 flex-1">
          <span class="flex items-center gap-2">
            <span class="font-medium text-highlighted">Monte Carlo com backtesting</span>
            <span
              class="eyebrow rounded-full border border-default px-1.5 py-px text-[10px] text-dimmed"
              aria-disabled="true"
            >Em breve</span>
          </span>
          <span class="block text-[12px] text-muted">Distribuição de cenários simulados sobre o histórico real, validada contra o que de fato aconteceu.</span>
        </span>
      </section>

      <NuxtLink
        to="/graficos"
        class="glass flex items-center gap-3 px-5 py-4 transition-colors hover:bg-muted"
      >
        <UIcon
          name="i-lucide-chart-candlestick"
          class="size-5 flex-none text-primary"
        />
        <span class="min-w-0 flex-1">
          <span class="block font-medium text-highlighted">Cenários no gráfico</span>
          <span class="block text-[12px] text-muted">Melhor caso, esperado e pior caso desenhados depois da linha de corte.</span>
        </span>
        <UIcon
          name="i-lucide-arrow-right"
          class="size-4 flex-none text-dimmed"
        />
      </NuxtLink>
    </div>

    <p class="text-[12px] text-dimmed">
      Leia as previsões como cenários, não como recomendação de compra ou venda.
    </p>
  </div>
</template>
