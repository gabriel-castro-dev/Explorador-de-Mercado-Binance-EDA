<script setup lang="ts">
import type { ButtonProps } from '@nuxt/ui'

const props = withDefaults(defineProps<{
  title: string
  description?: string
  icon?: string
  actions?: ButtonProps[]
}>(), { description: '', icon: 'i-lucide-layers', actions: () => [] })
</script>

<template>
  <div
    class="flex h-full min-h-[220px] flex-col items-center justify-center px-6 py-8 text-center"
    role="status"
  >
    <UIcon
      :name="props.icon"
      class="size-6 text-dimmed"
    />
    <h3 class="mt-3 text-[14px] font-semibold text-highlighted">
      {{ props.title }}
    </h3>
    <p
      v-if="props.description"
      class="mt-1.5 max-w-[420px] text-[13px] text-muted"
    >
      {{ props.description }}
    </p>
    <div
      v-if="props.actions.length"
      class="mt-4 flex flex-wrap items-center justify-center gap-2"
    >
      <UButton
        v-for="(action, i) in props.actions"
        :key="i"
        v-bind="action"
        size="sm"
      />
    </div>
  </div>
</template>
