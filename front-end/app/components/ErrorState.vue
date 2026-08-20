<script setup lang="ts">
const props = withDefaults(defineProps<{
  title: string
  description?: string
  /** Detalhe mono, ex.: `GET /klines/1h · 503`. */
  detail?: string
  retryLabel?: string
  retrying?: boolean
}>(), { description: '', detail: undefined, retryLabel: 'Tentar novamente', retrying: false })

const emit = defineEmits<{ (e: 'retry'): void }>()
const btn = ref<{ $el?: HTMLElement } | null>(null)

onMounted(() => {
  // Botão primário recebe foco ao aparecer (components.md)
  const el = btn.value?.$el
  if (el instanceof HTMLElement) el.focus({ preventScroll: true })
})
</script>

<template>
  <div
    class="flex h-full min-h-[220px] flex-col items-center justify-center px-6 py-8 text-center"
    role="alert"
  >
    <UIcon
      name="i-lucide-circle-x"
      class="size-6 text-danger"
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
    <div class="mt-4 flex flex-wrap items-center justify-center gap-3">
      <UButton
        ref="btn"
        icon="i-lucide-refresh-cw"
        :label="props.retryLabel"
        :loading="props.retrying"
        size="sm"
        @click="emit('retry')"
      />
      <span
        v-if="props.detail"
        class="num text-[11px] text-dimmed"
      >{{ props.detail }}</span>
    </div>
  </div>
</template>
