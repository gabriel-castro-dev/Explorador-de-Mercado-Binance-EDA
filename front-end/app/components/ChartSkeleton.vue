<script setup lang="ts">
const props = withDefaults(defineProps<{
  label?: string
  panes?: number
}>(), { label: 'Carregando…', panes: 1 })
</script>

<template>
  <div
    class="flex h-full w-full flex-col p-3"
    aria-busy="true"
    role="status"
  >
    <div class="flex gap-2">
      <USkeleton class="h-3 w-16" />
      <USkeleton class="h-3 w-40" />
    </div>
    <div class="mt-3 flex flex-1 gap-3">
      <USkeleton class="flex-1 rounded-md" />
      <div class="flex w-14 flex-col justify-between py-2">
        <USkeleton
          v-for="i in 6"
          :key="i"
          class="h-2.5 w-12"
        />
      </div>
    </div>
    <div
      v-for="i in Math.max(0, props.panes - 1)"
      :key="i"
      class="mt-3 flex gap-3"
    >
      <USkeleton class="h-[18%] min-h-[64px] flex-1 rounded-md" />
      <div class="w-14" />
    </div>
    <p class="num mt-3 text-[11px] text-dimmed">
      {{ props.label }}
    </p>
  </div>
</template>
