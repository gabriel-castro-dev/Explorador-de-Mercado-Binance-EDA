<script setup lang="ts">
import type { FreshnessState } from '~/composables/useFreshness'

/**
 * Declaração de frescor (Design.md §13.1). Nunca "live", "ao vivo" ou "tempo real".
 *
 * `line` é a forma padrão: faixa tipográfica aberta, como nos mockups.
 * `chip` é a cápsula, reservada a toolbars apertadas. Stale sempre ganha
 * dourado + ícone + texto — cor nunca é o único canal.
 */
const props = withDefaults(defineProps<{
  state: FreshnessState
  label: string
  prefix?: string
  variant?: 'line' | 'chip'
}>(), { prefix: 'SNAPSHOT', variant: 'line' })

const TOOLTIP = 'Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real.'

const stale = computed(() => props.state === 'stale')
</script>

<template>
  <UTooltip
    :text="TOOLTIP"
    :delay-duration="200"
  >
    <span
      tabindex="0"
      class="num inline-flex max-w-full items-center gap-2 rounded-md text-[11px] lg:text-[12px]"
      :class="[
        props.variant === 'chip' ? 'h-9 border px-3' : 'py-1',
        props.variant === 'chip'
          ? (stale ? 'border-[var(--cf-warn)]/50 bg-warn-soft text-warn' : 'border-default text-muted')
          : (stale ? 'text-warn' : 'text-muted'),
      ]"
      aria-live="polite"
    >
      <UIcon
        v-if="stale"
        name="i-lucide-triangle-alert"
        class="size-3.5 shrink-0"
        aria-hidden="true"
      />
      <span
        class="eyebrow shrink-0"
        :class="stale ? 'text-warn' : 'text-[var(--cf-electric)]'"
      >{{ props.prefix }}</span>
      <span
        class="shrink-0 text-dimmed"
        aria-hidden="true"
      >·</span>
      <USkeleton
        v-if="props.state === 'loading'"
        class="h-3 w-44"
      />
      <span
        v-else
        class="truncate"
      >{{ props.label }}</span>
    </span>
  </UTooltip>
</template>
