<script setup lang="ts">
import type { Timeframe } from '~/types/api'
import { TIMEFRAMES, TIMEFRAME_META } from '~/utils/constants'

/**
 * Timeframe (Design.md §15): compacto, ativo por linha — não por pill nem card.
 * Radios nativos dão navegação por setas e o par label/input sem custo de a11y.
 */
const model = defineModel<Timeframe>({ required: true })
const props = withDefaults(defineProps<{ showSubtitle?: boolean }>(), { showSubtitle: true })

const name = useId()
const subtitle = computed(() => TIMEFRAME_META[model.value].subtitle)
</script>

<template>
  <div class="flex items-center gap-4">
    <fieldset class="flex items-center">
      <legend class="sr-only">
        Timeframe
      </legend>
      <label
        v-for="tf in TIMEFRAMES"
        :key="tf"
        class="relative cursor-pointer"
      >
        <input
          v-model="model"
          type="radio"
          :name="name"
          :value="tf"
          class="peer sr-only"
        >
        <span
          class="num block min-h-9 px-3 py-2 text-[13px] text-muted transition-colors peer-checked:text-hi peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-[var(--cf-electric)] hover:text-default"
        >{{ TIMEFRAME_META[tf].label }}</span>
        <span
          class="absolute inset-x-2 bottom-0 h-[1.5px] origin-left scale-x-0 bg-[var(--cf-electric)] transition-transform duration-200 ease-[cubic-bezier(0.2,0.8,0.2,1)] peer-checked:scale-x-100"
          aria-hidden="true"
        />
      </label>
    </fieldset>

    <span
      v-if="props.showSubtitle"
      class="num hidden text-[11px] text-dimmed lg:inline"
    >{{ subtitle }}</span>
  </div>
</template>
