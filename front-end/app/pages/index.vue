<script setup lang="ts">
import type { InsightRow } from '~/utils/insights'
import { latestSnapshotAt } from '~/utils/tickers'
import { formatCompact, formatNumber } from '~/utils/format'

/**
 * Início — Home narrativa (Design.md §9). A ordem é narrativa → dados:
 * abertura editorial primeiro, faixas analíticas depois.
 *
 * Shim permanente: deep links antigos e o cookie de redirect pós-login apontavam
 * para `/?symbol=…` quando o gráfico morava aqui — esses caem em /graficos.
 */
const route = useRoute()
if (route.query.symbol) {
  await navigateTo({ path: '/graficos', query: route.query }, { replace: true })
}

useHead({ title: 'Início · CRYPTO FORECASTING' })

const { firstName } = useAccountIdentity()
const lastSeen = useLastSeen()
const lastSymbol = useLastSymbol()

const insights = useHomeInsights()
const reading = useDailyReading()

// Valor gravado por versões antigas/externas pode não ser um ISO válido.
const lastSeenValid = computed(() => (lastSeen.value && !Number.isNaN(Date.parse(lastSeen.value)) ? lastSeen.value : null))
const heading = computed(() => (lastSeenValid.value === null
  ? 'O mercado nas últimas 24 h'
  : 'As principais mudanças no mercado desde o seu último acesso'))

const snapshotAt = computed(() => latestSnapshotAt(insights.tickers.data.value))
const fresh = useFreshness('tickers', snapshotAt, () => insights.tickers.status.value)

const chartTarget = computed(() => (lastSymbol.value
  ? { path: '/graficos', query: { symbol: lastSymbol.value } }
  : { path: '/graficos' }))

const fmtAtr = (row: InsightRow) => `${formatNumber(row.value, 1)} %`
const fmtVolume = (row: InsightRow) => `${formatCompact(row.value)} USDT`
</script>

<template>
  <div>
    <HomeNarrativeOpening
      :first-name="firstName"
      :heading="heading"
      :last-seen-iso="lastSeenValid"
      :reading="reading.data.value"
      :reading-status="reading.status.value"
      :snapshot-state="fresh.state.value"
      :snapshot-label="fresh.label.value"
      @retry="reading.refresh()"
    />

    <!-- Mudanças do mercado — três faixas abertas (Design.md §9.2) -->
    <section
      class="cf-section cf-gutter cf-shell relative"
      aria-labelledby="mudancas-titulo"
    >
      <div
        v-reveal="{ y: 24 }"
        class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div>
          <h2
            id="mudancas-titulo"
            class="cf-h2 uppercase"
          >
            Mudanças do mercado
          </h2>
          <p class="mt-2 text-[15px] text-muted">
            Três leituras desde o seu último acesso.
          </p>
        </div>
        <SnapshotBadge
          prefix="SNAPSHOT"
          :state="fresh.state.value"
          :label="fresh.label.value"
        />
      </div>

      <div class="relative mt-14 md:mt-20">
        <HomeBandTrajectory />

        <div class="grid gap-14 md:gap-10 lg:grid-cols-3 lg:gap-12 xl:gap-16">
          <HomeMarketBand
            v-reveal="{ y: 32 }"
            :index="1"
            title="Maior volatilidade"
            subtitle="ATR 14 relativo"
            glyph="wave"
            :rows="insights.volatility.value"
            :status="insights.status.value"
            :format-value="fmtAtr"
            @retry="insights.refresh()"
          />
          <HomeMarketBand
            v-reveal="{ y: 32, delay: 80 }"
            :index="2"
            title="Gap real × projeção"
            subtitle="diferença entre preço real e previsão diária"
            glyph="curve"
            ai
            pending-model
            :rows="[]"
            :status="insights.status.value"
          />
          <HomeMarketBand
            v-reveal="{ y: 32, delay: 160 }"
            :index="3"
            title="Maior volume"
            subtitle="volume 24 h versus média de 7 dias"
            glyph="bars"
            :rows="insights.volume.value"
            :status="insights.status.value"
            :format-value="fmtVolume"
            @retry="insights.refresh()"
          />
        </div>
      </div>

      <div
        v-reveal="{ y: 20 }"
        class="mt-16 flex flex-wrap items-center gap-x-6 gap-y-3 md:mt-20"
      >
        <NuxtLink
          to="/mercado"
          class="cf-navlink eyebrow inline-flex min-h-11 items-center text-muted hover:text-default"
        >
          VER TOP 20
        </NuxtLink>
        <span
          class="h-4 w-px bg-[var(--cf-hairline)]"
          aria-hidden="true"
        />
        <NuxtLink
          :to="chartTarget"
          class="cf-navlink eyebrow inline-flex min-h-11 items-center gap-2.5 text-muted hover:text-default"
        >
          CONTINUAR NO GRÁFICO
          <UIcon
            name="i-lucide-arrow-right"
            class="size-4"
            aria-hidden="true"
          />
        </NuxtLink>
      </div>

      <p class="mt-10 max-w-[62ch] text-[13px] text-dimmed">
        Leia as previsões como cenários, não como recomendação de compra ou venda.
      </p>
    </section>
  </div>
</template>
