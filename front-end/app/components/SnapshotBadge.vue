<script setup lang="ts">
import type { FreshnessState } from '~/composables/useFreshness'

/** Selo de snapshot (ux-spec §1/§6): mono, caixa alta, ponto de estado; nunca "live". */
const props = withDefaults(defineProps<{
  state: FreshnessState
  label: string
  prefix?: string
}>(), { prefix: 'SNAPSHOT' })

const tooltip = 'Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real.'
</script>

<template>
  <UTooltip
    :text="tooltip"
    :delay-duration="200"
  >
    <span
      tabindex="0"
      class="num inline-flex h-8 max-w-full items-center gap-2 rounded-md border px-2.5 text-[11px]"
      :class="props.state === 'stale' ? 'border-(--cf-warning)/50 bg-warn text-warn' : 'border-default bg-elevated text-muted'"
      aria-live="polite"
    >
      <UIcon
        v-if="props.state === 'stale'"
        name="i-lucide-triangle-alert"
        class="size-3.5 shrink-0"
        aria-hidden="true"
      />
      <span
        v-else
        class="inline-block size-1.5 shrink-0 rounded-full"
        :class="props.state === 'fresh' ? 'bg-(--cf-up)' : 'bg-(--ui-text-dimmed)'"
        aria-hidden="true"
      />
      <span class="eyebrow shrink-0">{{ props.prefix }}</span>
      <span
        class="h-3.5 w-px shrink-0 bg-(--ui-border)"
        aria-hidden="true"
      />
      <USkeleton
        v-if="props.state === 'loading'"
        class="h-3 w-40"
      />
      <span
        v-else
        class="truncate"
      >{{ props.label }}</span>
    </span>
  </UTooltip>
</template>
