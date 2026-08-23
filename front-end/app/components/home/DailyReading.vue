<script setup lang="ts">
import type { DailyReading } from '~/types/api'
import { formatUtcShort } from '~/utils/format'

type Status = 'idle' | 'pending' | 'success' | 'error'

const props = defineProps<{
  reading: DailyReading | null
  status: Status
}>()

const emit = defineEmits<{ (e: 'retry'): void }>()
</script>

<template>
  <!-- Único glass-hi da tela (máx. 1 glow por tela — Design.md §4) -->
  <section
    class="glass-hi flex items-start gap-4 px-5 py-4"
    aria-label="Leitura do dia"
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
          Leitura do dia, pelo modelo
        </h2>
        <span class="ai-chip text-[10px]">IA · v0 · em validação</span>
        <span
          v-if="props.reading"
          class="num ml-auto text-[11px] text-dimmed"
        >gerada {{ formatUtcShort(props.reading.generated_at) }} UTC</span>
      </div>

      <div
        v-if="props.status === 'pending' && !props.reading"
        class="mt-2 space-y-1.5"
      >
        <USkeleton class="h-3.5 w-full" />
        <USkeleton class="h-3.5 w-4/5" />
      </div>

      <div
        v-else-if="!props.reading"
        class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1"
        role="status"
      >
        <p class="text-[13px] text-muted">
          A leitura do dia está indisponível no momento.
        </p>
        <UButton
          variant="link"
          size="xs"
          label="Tentar novamente"
          class="p-0"
          @click="emit('retry')"
        />
      </div>

      <template v-else>
        <p class="mt-1 max-w-[110ch] text-[13px] text-muted">
          {{ props.reading.text }}
        </p>
        <p class="mt-2 text-[11.5px] text-dimmed">
          {{ props.reading.disclaimer }}
        </p>
      </template>
    </div>
  </section>
</template>
