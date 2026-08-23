<script setup lang="ts">
import type { InsightRow } from '~/utils/insights'
import { symbolName } from '~/utils/constants'

type Status = 'idle' | 'pending' | 'success' | 'error'

const props = withDefaults(defineProps<{
  icon: string
  title: string
  subtitle: string
  rows: readonly InsightRow[]
  status: Status
  /** Card de conteúdo do modelo: ícone/chip em ciano (exclusivo de IA). */
  ai?: boolean
  /** Sem dados do modelo ainda (marco 3): estado final com chip, sem números. */
  aiPending?: boolean
  /** Formata o valor principal da linha. */
  formatValue?: (row: InsightRow) => string
  /** Formata a variação de apoio; null = sem delta. */
  formatDelta?: (row: InsightRow) => string | null
}>(), {
  ai: false,
  aiPending: false,
  formatValue: (row: InsightRow) => String(row.value),
  formatDelta: () => null,
})

const emit = defineEmits<{ (e: 'retry'): void }>()

function deltaTone(row: InsightRow): string {
  if (props.ai) return 'text-ai'
  if (row.delta === null || row.delta === 0) return 'text-flat'
  return row.delta > 0 ? 'text-up' : 'text-down'
}
</script>

<template>
  <section
    class="glass flex min-w-0 flex-1 flex-col overflow-hidden"
    :aria-label="props.title"
  >
    <div class="flex items-center gap-2.5 border-b border-[var(--cf-border-muted)] px-4 py-3">
      <span
        class="inline-flex size-8 flex-none items-center justify-center rounded-lg border"
        :class="props.ai
          ? 'border-[rgba(95,196,255,.35)] bg-[rgba(95,196,255,.10)] text-ai'
          : 'border-[rgba(62,134,247,.3)] bg-primary-soft text-primary'"
      >
        <UIcon
          :name="props.icon"
          class="size-4"
        />
      </span>
      <span class="min-w-0 flex-1">
        <span class="block truncate font-bold text-highlighted">{{ props.title }}</span>
        <span class="block truncate text-[11.5px] text-muted">{{ props.subtitle }}</span>
      </span>
      <span
        v-if="props.ai"
        class="ai-chip text-[10px]"
      >IA · v0</span>
    </div>

    <!-- Bloco de IA sem modelo publicado: estado final honesto, sem números -->
    <div
      v-if="props.aiPending"
      class="flex flex-1 flex-col items-center justify-center gap-1.5 px-4 py-8 text-center"
      role="status"
    >
      <span class="ai-chip">IA · v0 · em validação</span>
      <p class="max-w-[30ch] text-[12.5px] text-muted">
        O modelo ainda não publicou previsões. Este ranking estreia com o marco de ML.
      </p>
    </div>

    <div
      v-else-if="props.status === 'pending' && !props.rows.length"
      class="space-y-2.5 px-4 py-3"
    >
      <USkeleton
        v-for="i in 5"
        :key="i"
        class="h-8 w-full"
      />
    </div>

    <div
      v-else-if="props.status === 'error' && !props.rows.length"
      class="flex flex-1 items-center justify-between gap-3 px-4 py-6 text-[13px] text-muted"
      role="alert"
    >
      Ranking indisponível.
      <UButton
        variant="link"
        size="xs"
        label="Tentar novamente"
        class="p-0"
        @click="emit('retry')"
      />
    </div>

    <p
      v-else-if="!props.rows.length"
      class="px-4 py-6 text-[13px] text-muted"
      role="status"
    >
      Sem dados suficientes para este ranking hoje.
    </p>

    <ol
      v-else
      class="flex flex-col"
    >
      <li
        v-for="(row, i) in props.rows"
        :key="row.symbol"
        class="border-b border-[var(--cf-border-muted)] last:border-b-0"
      >
        <NuxtLink
          :to="{ path: '/graficos', query: { symbol: row.symbol } }"
          class="flex items-center gap-2.5 px-4 py-2 transition-colors hover:bg-muted"
        >
          <span class="num w-4 flex-none text-[11px] text-dimmed">{{ i + 1 }}</span>
          <span class="min-w-0 flex-1">
            <span
              class="num block truncate text-[13px] font-medium text-highlighted"
              translate="no"
            >{{ row.symbol }}</span>
            <span class="block truncate text-[11px] text-muted">{{ symbolName(row.symbol) ?? '' }}</span>
          </span>
          <span class="flex flex-col items-end">
            <span class="num text-[13px] text-default">{{ props.formatValue(row) }}</span>
            <span
              v-if="props.formatDelta(row)"
              class="num text-[11.5px]"
              :class="deltaTone(row)"
            >{{ props.formatDelta(row) }}</span>
          </span>
        </NuxtLink>
      </li>
    </ol>
  </section>
</template>
