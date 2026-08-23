<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { ScenarioCell, ScenarioRow } from '~/types/forecast'
import type { SortDir } from '~/utils/tickers'
import { sortScenarioRows, type ScenarioSortKey } from '~/utils/forecast-table'
import { symbolName } from '~/utils/constants'
import { EM_DASH, formatNumber, formatPercent, formatPrice } from '~/utils/format'

/**
 * Cenários por ativo (Design.md §11.2): full-bleed dentro das margens, sem card
 * externo e sem cantos arredondados. Hairlines, Geist Mono nos cabeçalhos e
 * números, wash horizontal na linha ativa.
 */
const props = defineProps<{
  rows: readonly ScenarioRow[]
  refreshing?: boolean
}>()

const emit = defineEmits<{ (e: 'refresh'): void }>()

const isMobile = useMediaQuery('(max-width: 767px)')

const COLUMNS: { key: ScenarioSortKey, label: string, align: 'start' | 'end' }[] = [
  { key: 'symbol', label: 'Ativo', align: 'start' },
  { key: 'realPrice', label: 'Preço real', align: 'start' },
  { key: 'daily', label: 'Diário', align: 'start' },
  { key: 'weekly', label: 'Semanal', align: 'start' },
  { key: 'monthly', label: 'Mensal', align: 'start' },
  { key: 'yearly', label: 'Anual', align: 'start' },
  { key: 'confidence', label: 'Confiança', align: 'start' },
]

const sortKey = ref<ScenarioSortKey>('confidence')
const sortDir = ref<SortDir>('desc')
const sorted = computed(() => sortScenarioRows(props.rows, sortKey.value, sortDir.value))
const expanded = ref<string | null>(null)

function toggleSort(key: ScenarioSortKey) {
  if (sortKey.value === key) sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  else {
    sortKey.value = key
    sortDir.value = key === 'symbol' ? 'asc' : 'desc'
  }
}

function ariaSort(key: ScenarioSortKey): 'ascending' | 'descending' | 'none' {
  if (sortKey.value !== key) return 'none'
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

/**
 * `114.890 · +1,2 %`. Null vira `—`; zero real continua `0` (via formatPercent).
 * Negativo em vermelho; positivos em ciano — cor nunca é o único canal, o sinal
 * `+`/`−` acompanha sempre.
 */
function cellText(cell: ScenarioCell): string {
  if (cell.price === null && cell.changePercent === null) return EM_DASH
  return `${formatPrice(cell.price)} · ${formatPercent(cell.changePercent, 1)}`
}

function cellTone(cell: ScenarioCell): string {
  if (cell.changePercent === null) return 'text-dimmed'
  return cell.changePercent < 0 ? 'text-down' : 'text-ai'
}

const sortLabel = computed(() => {
  const column = COLUMNS.find(c => c.key === sortKey.value)
  return `ORDENAR: ${(column?.label ?? '').toUpperCase()} ${sortDir.value === 'desc' ? '↓' : '↑'}`
})

function chartLink(symbol: string) {
  return { path: '/graficos', query: { symbol } }
}
</script>

<template>
  <section aria-labelledby="cenarios-titulo">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h2
          id="cenarios-titulo"
          class="cf-h2 uppercase"
        >
          Cenários por ativo
        </h2>
        <p class="mt-2 text-[15px] text-muted">
          <span class="num">{{ formatNumber(props.rows.length, 0) }}</span> ativos · horizontes diário,
          semanal, mensal e anual · valores em USDT
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-x-6 gap-y-2">
        <span class="num text-[11px] tracking-[0.08em] text-dimmed">{{ sortLabel }}</span>
        <UButton
          color="neutral"
          variant="ghost"
          size="sm"
          icon="i-lucide-refresh-cw"
          :loading="props.refreshing"
          label="Atualizar"
          @click="emit('refresh')"
        />
      </div>
    </div>

    <!-- Vazio: cabeçalho preservado + motivo provável (Design.md §13.2/§13.3) -->
    <div
      v-if="!props.rows.length"
      class="mt-8"
    >
      <div class="cf-hairline-b flex gap-6 overflow-x-auto pb-3">
        <span
          v-for="column in COLUMNS"
          :key="column.key"
          class="eyebrow shrink-0 text-dimmed"
        >{{ column.label }}</span>
      </div>
      <p
        class="mt-6 max-w-[56ch] text-[15px] text-muted"
        role="status"
      >
        O modelo ainda não publicou previsões para este ativo.
      </p>
      <p class="mt-2 max-w-[56ch] text-[13px] text-dimmed">
        Quando a primeira rodada sair, cada linha traz o preço real, o valor projetado
        e a variação em cada horizonte, mais a confiança medida no backtesting.
      </p>
    </div>

    <!-- Mobile: linha expansível, sem card decorativo -->
    <ul
      v-else-if="isMobile"
      class="mt-7"
    >
      <li
        v-for="row in sorted"
        :key="row.symbol"
        class="cf-rule"
      >
        <div class="flex items-center gap-3 py-3.5">
          <NuxtLink
            :to="chartLink(row.symbol)"
            class="num min-w-0 flex-1 truncate text-[15px] text-hi"
            translate="no"
          >
            {{ row.symbol }}
            <span class="sr-only">— abrir {{ symbolName(row.symbol) ?? row.symbol }} nos gráficos</span>
          </NuxtLink>
          <span
            class="num shrink-0 text-[14px]"
            :class="cellTone(row.daily)"
          >{{ cellText(row.daily) }}</span>
          <span class="num shrink-0 text-[14px] text-ai">{{ row.confidence === null ? EM_DASH : `${formatNumber(row.confidence, 0)} %` }}</span>
          <button
            type="button"
            class="-me-1.5 flex size-11 shrink-0 items-center justify-center rounded-md text-muted"
            :aria-expanded="expanded === row.symbol"
            :aria-label="`Mostrar semanal, mensal e anual de ${row.symbol}`"
            @click="expanded = expanded === row.symbol ? null : row.symbol"
          >
            <UIcon
              :name="expanded === row.symbol ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
              class="size-4"
              aria-hidden="true"
            />
          </button>
        </div>
        <dl
          v-if="expanded === row.symbol"
          class="pb-4"
        >
          <div
            v-for="entry in [
              { label: 'Preço real', text: formatPrice(row.realPrice), tone: 'text-default' },
              { label: 'Semanal', text: cellText(row.weekly), tone: cellTone(row.weekly) },
              { label: 'Mensal', text: cellText(row.monthly), tone: cellTone(row.monthly) },
              { label: 'Anual', text: cellText(row.yearly), tone: cellTone(row.yearly) },
            ]"
            :key="entry.label"
            class="flex items-baseline justify-between gap-4 py-1.5"
          >
            <dt class="eyebrow text-dimmed">
              {{ entry.label }}
            </dt>
            <dd
              class="num text-[14px]"
              :class="entry.tone"
            >
              {{ entry.text }}
            </dd>
          </div>
        </dl>
      </li>
    </ul>

    <!-- Desktop: tabela full-bleed -->
    <div
      v-else
      class="mt-7 overflow-x-auto"
    >
      <table class="w-full min-w-[980px] border-collapse text-[14px]">
        <caption class="sr-only">
          Cenários por ativo, ordenado por {{ sortLabel.toLowerCase() }}. Valores em USDT, variação em porcentagem.
        </caption>
        <thead>
          <tr class="cf-hairline-b">
            <th
              v-for="column in COLUMNS"
              :key="column.key"
              scope="col"
              :aria-sort="ariaSort(column.key)"
              class="py-3 pe-6 text-start whitespace-nowrap"
            >
              <button
                type="button"
                class="eyebrow inline-flex min-h-9 items-center gap-1.5 rounded-sm"
                :class="sortKey === column.key ? 'text-hi' : 'text-dimmed hover:text-muted'"
                @click="toggleSort(column.key)"
              >
                {{ column.label }}
                <UIcon
                  v-if="sortKey === column.key"
                  :name="sortDir === 'desc' ? 'i-lucide-arrow-down' : 'i-lucide-arrow-up'"
                  class="size-3"
                  aria-hidden="true"
                />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in sorted"
            :key="row.symbol"
            class="cf-rule transition-colors hover:cf-row-hover focus-within:cf-row-hover"
          >
            <td class="py-3.5 pe-6 whitespace-nowrap">
              <NuxtLink
                :to="chartLink(row.symbol)"
                class="num rounded-sm text-[15px] text-hi"
                translate="no"
              >
                {{ row.symbol }}
                <span class="sr-only">— abrir {{ symbolName(row.symbol) ?? row.symbol }} nos gráficos</span>
              </NuxtLink>
            </td>
            <td class="num py-3.5 pe-6 whitespace-nowrap text-default">
              {{ formatPrice(row.realPrice) }}
            </td>
            <td
              v-for="key in (['daily', 'weekly', 'monthly', 'yearly'] as const)"
              :key="key"
              class="num py-3.5 pe-6 whitespace-nowrap"
              :class="cellTone(row[key])"
            >
              {{ cellText(row[key]) }}
            </td>
            <td class="py-3.5 whitespace-nowrap">
              <span class="num text-ai">{{ row.confidence === null ? EM_DASH : `${formatNumber(row.confidence, 0)} %` }}</span>
              <span
                v-if="row.confidence !== null"
                class="mt-1.5 block h-px w-[92px] bg-[var(--cf-hairline)]"
                aria-hidden="true"
              >
                <span
                  class="block h-px bg-[var(--cf-cyan)]"
                  :style="{ width: `${Math.min(100, Math.max(0, row.confidence))}%` }"
                />
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="cf-hairline-t mt-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-2 pt-4">
      <p class="text-[13px] text-dimmed">
        Cenários, não recomendações · o erro cresce com o horizonte
      </p>
      <p
        v-if="props.rows.length"
        class="num text-[11px] tracking-[0.08em] text-dimmed"
      >
        MOSTRANDO {{ formatNumber(sorted.length, 0) }} DE {{ formatNumber(props.rows.length, 0) }}
      </p>
    </div>
  </section>
</template>
