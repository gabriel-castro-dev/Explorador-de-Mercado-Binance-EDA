<script setup lang="ts">
import type { LineStyleName } from '~/utils/constants'

/** Amostra de série: cor + estilo de traço real (codificação secundária; decorativa). */
const props = withDefaults(defineProps<{
  color: string
  styleName?: LineStyleName
  kind?: 'line' | 'bars'
  width?: number
}>(), { styleName: 'solid', kind: 'line', width: 18 })

const borderStyle = computed(() => (props.styleName === 'dashed' ? 'dashed' : props.styleName === 'dotted' ? 'dotted' : 'solid'))
</script>

<template>
  <span
    v-if="props.kind === 'bars'"
    class="inline-flex h-3 items-end gap-px"
    :style="{ width: `${props.width}px` }"
    aria-hidden="true"
  >
    <span
      v-for="(h, i) in [5, 9, 7, 11, 6]"
      :key="i"
      class="flex-1 rounded-[1px]"
      :style="{ height: `${h}px`, backgroundColor: props.color, opacity: 0.7 }"
    />
  </span>
  <span
    v-else
    class="inline-block border-t-2"
    :style="{ width: `${props.width}px`, borderColor: props.color, borderTopStyle: borderStyle }"
    aria-hidden="true"
  />
</template>
