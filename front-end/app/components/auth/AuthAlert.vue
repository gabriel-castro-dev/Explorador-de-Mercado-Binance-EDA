<script setup lang="ts">
/** Erro/aviso acima dos campos: role=alert e foco ao aparecer (ux-spec §3). */
const props = withDefaults(defineProps<{
  message: string | null | undefined
  hint?: string | null
  tone?: 'error' | 'status'
}>(), { hint: null, tone: 'error' })

const el = ref<HTMLElement | null>(null)
watch(() => props.message, async (m) => {
  if (m && props.tone === 'error') {
    await nextTick()
    el.value?.focus()
  }
})
</script>

<template>
  <div
    v-if="props.message"
    ref="el"
    tabindex="-1"
    :role="props.tone === 'error' ? 'alert' : 'status'"
    class="rounded-md border px-3 py-2.5 text-[13px] outline-none"
    :class="props.tone === 'error' ? 'border-(--cf-danger)/40 bg-(--cf-danger-bg) text-(--cf-danger)' : 'border-default bg-muted text-default'"
  >
    <div class="flex items-start gap-2">
      <UIcon
        :name="props.tone === 'error' ? 'i-lucide-circle-alert' : 'i-lucide-check-circle-2'"
        class="mt-0.5 size-4 shrink-0"
      />
      <div>
        <p>{{ props.message }}</p>
        <p
          v-if="props.hint"
          class="mt-1 text-[12px] opacity-80"
        >
          {{ props.hint }}
        </p>
      </div>
    </div>
  </div>
</template>
