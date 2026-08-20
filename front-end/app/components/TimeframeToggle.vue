<script setup lang="ts">
import type { Timeframe } from '~/types/api'
import { TIMEFRAMES, TIMEFRAME_META } from '~/utils/constants'

const model = defineModel<Timeframe>({ required: true })
const props = withDefaults(defineProps<{ showSubtitle?: boolean }>(), { showSubtitle: true })

const items = TIMEFRAMES.map(tf => ({ label: TIMEFRAME_META[tf].label, value: tf }))
const subtitle = computed(() => TIMEFRAME_META[model.value].subtitle)
</script>

<template>
  <div class="flex items-center gap-3">
    <UTabs
      v-model="model"
      :items="items"
      :content="false"
      variant="pill"
      size="sm"
      color="neutral"
      aria-label="Timeframe"
      :ui="{ list: 'rounded-md bg-muted p-0.5', trigger: 'num w-12 text-[12px] data-[state=active]:text-highlighted', indicator: 'rounded-[5px] bg-elevated shadow-none ring ring-default' }"
    />
    <span
      v-if="props.showSubtitle"
      class="num hidden text-[11px] text-dimmed lg:inline"
    >{{ subtitle }}</span>
  </div>
</template>
