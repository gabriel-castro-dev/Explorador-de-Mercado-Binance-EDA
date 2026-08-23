<script setup lang="ts">
import type { InsightRow } from '~/utils/insights'
import type { AsyncStatus } from '~/utils/async-state'
import { asyncView } from '~/utils/async-state'
import { symbolName } from '~/utils/constants'

/**
 * Uma das três faixas de "Mudanças do mercado" (Design.md §9.2).
 * Faixa aberta: numeral estrutural, título, explicação e até cinco linhas.
 * Nenhum card — só macroespaço e hairlines.
 */
const props = withDefaults(defineProps<{
  index: number
  title: string
  subtitle: string
  glyph: 'wave' | 'curve' | 'bars'
  rows: readonly InsightRow[]
  status: AsyncStatus
  /** Conteúdo do modelo: ganha o selo `IA · v0 · EM VALIDAÇÃO` e ciano nos valores. */
  ai?: boolean
  /** O modelo ainda não publicou esta leitura: estado honesto, sem números. */
  pendingModel?: boolean
  formatValue?: (row: InsightRow) => string
  valueTone?: (row: InsightRow) => 'up' | 'down' | 'flat' | 'ai' | 'plain'
}>(), {
  ai: false,
  pendingModel: false,
  formatValue: (row: InsightRow) => String(row.value),
  valueTone: () => 'plain' as const,
})

const emit = defineEmits<{ (e: 'retry'): void }>()

const MOBILE_LIMIT = 2
const expanded = ref(false)
const stagger = useStagger(60)

const view = computed(() => (props.pendingModel ? 'model-pending' : asyncView(props.status, props.rows.length > 0)))
const visibleRows = computed(() => props.rows.slice(0, 5))
const numeral = computed(() => String(props.index).padStart(2, '0'))

function toneClass(row: InsightRow) {
  return {
    up: 'text-up',
    down: 'text-down',
    flat: 'text-flat',
    ai: 'text-ai',
    plain: 'text-hi',
  }[props.valueTone(row)]
}

const listId = useId()
</script>

<template>
  <section
    class="relative min-w-0"
    :aria-labelledby="`${listId}-title`"
  >
    <div class="flex items-start gap-4 md:gap-5">
      <span
        class="num shrink-0 text-[44px] leading-none font-medium text-[var(--cf-text-dim)]/45 md:text-[56px]"
        aria-hidden="true"
      >{{ numeral }}</span>

      <div class="min-w-0 pt-1">
        <svg
          class="mb-3 h-5 w-[64px] text-[var(--cf-electric)]"
          viewBox="0 0 64 20"
          fill="none"
          aria-hidden="true"
        >
          <path
            v-if="props.glyph === 'wave'"
            d="M1 12 L8 12 L11 4 L15 17 L19 8 L23 13 L27 10 L34 10 L38 6 L42 14 L46 11 L63 11"
            stroke="currentColor"
            stroke-width="1.4"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <template v-else-if="props.glyph === 'curve'">
            <path
              d="M1 16 C14 16 18 5 30 5 C42 5 46 11 56 11"
              stroke="currentColor"
              stroke-width="1.4"
              stroke-linecap="round"
            />
            <circle
              cx="58"
              cy="11"
              r="3"
              fill="currentColor"
            />
          </template>
          <template v-else>
            <rect
              v-for="(h, i) in [7, 13, 5, 17, 10]"
              :key="i"
              :x="1 + i * 8"
              :y="19 - h"
              width="4"
              :height="h"
              rx="1"
              fill="currentColor"
            />
          </template>
        </svg>

        <h3
          :id="`${listId}-title`"
          class="flex flex-wrap items-baseline gap-x-2.5 gap-y-1 text-[15px] font-medium tracking-[0.06em] text-hi uppercase md:text-[16px]"
        >
          {{ props.title }}
          <span
            v-if="props.ai"
            class="num text-[10px] tracking-[0.1em] text-ai normal-case"
          >IA · v0 · EM VALIDAÇÃO</span>
        </h3>
        <p class="mt-1.5 text-[13px] text-muted">
          {{ props.subtitle }}
        </p>
      </div>
    </div>

    <!-- Linhas -->
    <div class="mt-7">
      <div
        v-if="view === 'loading' || view === 'idle'"
        class="space-y-0"
        role="status"
        aria-busy="true"
      >
        <div
          v-for="i in 4"
          :key="i"
          class="cf-rule flex items-center justify-between gap-4 py-3.5"
        >
          <USkeleton class="h-3.5 w-28" />
          <USkeleton class="h-3.5 w-16" />
        </div>
        <span class="sr-only">Carregando {{ props.title.toLowerCase() }}…</span>
      </div>

      <div
        v-else-if="view === 'model-pending'"
        class="cf-hairline-t max-w-[38ch] pt-5"
        role="status"
      >
        <p class="text-[14px] text-muted">
          O modelo ainda não publicou previsões para este ativo.
        </p>
        <p class="mt-2 text-[13px] text-dimmed">
          Esta leitura estreia com a primeira rodada de previsões.
        </p>
      </div>

      <div
        v-else-if="view === 'error'"
        class="cf-hairline-t flex flex-wrap items-center gap-x-3 gap-y-1 pt-5 text-[14px] text-muted"
        role="alert"
      >
        <span>Não foi possível carregar este ranking.</span>
        <UButton
          variant="link"
          size="xs"
          class="p-0"
          label="Tentar novamente"
          @click="emit('retry')"
        />
      </div>

      <p
        v-else-if="view === 'empty'"
        class="cf-hairline-t max-w-[38ch] pt-5 text-[14px] text-muted"
        role="status"
      >
        Sem dados suficientes para este ranking no snapshot de hoje.
      </p>

      <ol v-else>
        <li
          v-for="(row, i) in visibleRows"
          :key="row.symbol"
          v-reveal="{ delay: stagger(i), y: 14 }"
          class="cf-rule"
          :class="i >= MOBILE_LIMIT && !expanded ? 'hidden md:block' : ''"
        >
          <NuxtLink
            :to="{ path: '/graficos', query: { symbol: row.symbol } }"
            class="group flex min-h-11 items-center gap-4 py-3 transition-colors hover:bg-[var(--cf-electric)]/6 focus-visible:bg-[var(--cf-electric)]/6"
          >
            <span
              class="num w-4 shrink-0 text-[12px] text-dimmed"
              aria-hidden="true"
            >{{ i + 1 }}</span>
            <span class="min-w-0 flex-1">
              <span
                class="num block truncate text-[15px] tracking-[0.02em] text-hi"
                translate="no"
              >{{ row.symbol }}</span>
              <span class="sr-only">{{ symbolName(row.symbol) ?? row.symbol }}</span>
            </span>
            <span
              class="num shrink-0 text-[15px]"
              :class="toneClass(row)"
            >{{ props.formatValue(row) }}</span>
          </NuxtLink>
        </li>
      </ol>

      <UButton
        v-if="view === 'ready' && visibleRows.length > MOBILE_LIMIT && !expanded"
        class="mt-3 p-0 md:hidden"
        variant="link"
        color="neutral"
        size="sm"
        :label="`Ver top ${visibleRows.length}`"
        trailing-icon="i-lucide-chevron-down"
        @click="expanded = true"
      />
    </div>
  </section>
</template>
