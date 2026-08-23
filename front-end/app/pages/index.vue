<script setup lang="ts">
import type { InsightRow } from '~/utils/insights'
import { latestSnapshotAt } from '~/utils/tickers'
import { arrowOf, formatCompact, formatNumber, formatPercent, formatUtcShort } from '~/utils/format'

/**
 * Início (home de insights — Design.md §5). Shim permanente: deep links antigos
 * e o cookie de redirect pós-login apontavam para `/?symbol=…` quando o gráfico
 * morava aqui — esses caem direto em /graficos com a mesma query.
 */
const route = useRoute()
if (route.query.symbol) {
  await navigateTo({ path: '/graficos', query: route.query }, { replace: true })
}

useHead({ title: 'Início · crypto forecasting' })

const user = useSupabaseUser()
const prefs = usePreferences()
const lastSeen = useLastSeen()
const lastSymbol = useLastSymbol()

const insights = useHomeInsights()
const reading = useDailyReading()

const firstName = computed(() => {
  const name = prefs.form.displayName.trim()
  if (name) return name.split(/\s+/)[0]
  const email = (user.value?.email as string | undefined) ?? ''
  return email.split('@')[0] || 'de volta'
})

// Valor gravado por versões antigas/externas pode não ser um ISO válido.
const lastSeenValid = computed(() => (lastSeen.value && !Number.isNaN(Date.parse(lastSeen.value)) ? lastSeen.value : null))
const isFirstVisit = computed(() => lastSeenValid.value === null)
const heading = computed(() => (isFirstVisit.value
  ? 'O mercado nas últimas 24 h'
  : 'As principais mudanças no mercado desde o seu último acesso'))

const snapshotAt = computed(() => latestSnapshotAt(insights.tickers.data.value))
const fresh = useFreshness('tickers', snapshotAt, () => insights.tickers.status.value)

const refreshing = ref(false)
async function refreshAll() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    await Promise.all([insights.refresh(), reading.refresh()])
  } finally {
    refreshing.value = false
  }
}

const fmtAtr = (row: InsightRow) => `ATR ${formatNumber(row.value, 1)} %`
const fmtAtrDelta = (row: InsightRow) => (row.delta === null ? null : `${arrowOf(row.delta)} ${formatPercent(row.delta)}`.trim())
const fmtVolume = (row: InsightRow) => `${formatCompact(row.value)} USDT`
const fmtVolumeDelta = (row: InsightRow) => (row.delta === null ? null : `${arrowOf(row.delta)} ${formatPercent(row.delta)} vs média`.trim())
</script>

<template>
  <div class="space-y-4">
    <!-- Cabeçalho -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="eyebrow text-ai">
          Bem-vindo novamente, {{ firstName }}
        </p>
        <h1 class="mt-1.5 text-[24px] font-bold tracking-[-.01em] text-highlighted">
          {{ heading }}
        </h1>
        <p
          v-if="lastSeenValid"
          class="num mt-1.5 text-[12px] text-muted"
        >
          Último acesso em {{ formatUtcShort(lastSeenValid) }} UTC
        </p>
      </div>
      <div class="flex items-center gap-2">
        <SnapshotBadge
          prefix="RESUMO 24H"
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
          @click="refreshAll"
        />
      </div>
    </div>

    <!-- Top-5: volatilidade · gap real × projeção (IA) · volume -->
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <HomeInsightCard
        icon="i-lucide-activity"
        title="Maior volatilidade de preço"
        subtitle="ATR 14 relativo · último snapshot diário"
        :rows="insights.volatility.value"
        :status="insights.status.value"
        :format-value="fmtAtr"
        :format-delta="fmtAtrDelta"
        @retry="insights.refresh()"
      />
      <HomeInsightCard
        icon="i-lucide-git-compare-arrows"
        title="Maior gap real × projeção"
        subtitle="diferença entre preço real e previsão diária"
        ai
        ai-pending
        :rows="[]"
        :status="insights.status.value"
      />
      <HomeInsightCard
        icon="i-lucide-bar-chart-3"
        title="Maior volume de transação"
        subtitle="volume 24h em USDT vs média de 7 dias"
        :rows="insights.volume.value"
        :status="insights.status.value"
        :format-value="fmtVolume"
        :format-delta="fmtVolumeDelta"
        @retry="insights.refresh()"
      />
    </div>

    <!-- Leitura do dia (IA) -->
    <HomeDailyReading
      :reading="reading.data.value"
      :status="reading.status.value"
      @retry="reading.refresh()"
    />

    <!-- Atalhos -->
    <div class="grid gap-4 sm:grid-cols-2">
      <NuxtLink
        :to="lastSymbol ? { path: '/graficos', query: { symbol: lastSymbol } } : '/graficos'"
        class="glass flex items-center gap-3 px-5 py-4 transition-colors hover:bg-muted"
      >
        <UIcon
          name="i-lucide-chart-candlestick"
          class="size-5 flex-none text-primary"
        />
        <span class="min-w-0 flex-1">
          <span class="block font-medium text-highlighted">Continuar de onde parou</span>
          <span class="num block truncate text-[12px] text-muted">{{ lastSymbol || 'Abrir os gráficos' }}</span>
        </span>
        <UIcon
          name="i-lucide-arrow-right"
          class="size-4 flex-none text-dimmed"
        />
      </NuxtLink>
      <NuxtLink
        to="/preferencias"
        class="glass flex items-center gap-3 px-5 py-4 transition-colors hover:bg-muted"
      >
        <UIcon
          name="i-lucide-bell"
          class="size-5 flex-none text-primary"
        />
        <span class="min-w-0 flex-1">
          <span class="block font-medium text-highlighted">Configurar alertas</span>
          <span class="block truncate text-[12px] text-muted">Tópicos e canal do resumo diário</span>
        </span>
        <UIcon
          name="i-lucide-arrow-right"
          class="size-4 flex-none text-dimmed"
        />
      </NuxtLink>
    </div>
  </div>
</template>
