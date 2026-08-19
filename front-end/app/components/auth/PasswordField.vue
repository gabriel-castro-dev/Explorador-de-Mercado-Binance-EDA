<script setup lang="ts">
const props = withDefaults(defineProps<{
  autocomplete?: 'current-password' | 'new-password'
  showStrength?: boolean
  placeholder?: string
}>(), { autocomplete: 'current-password', showStrength: false, placeholder: '' })

const model = defineModel<string>({ default: '' })
const visible = ref(false)

const strength = computed(() => {
  const v = model.value ?? ''
  if (!v) return null
  let score = 0
  if (v.length >= 8) score++
  if (v.length >= 12) score++
  if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++
  if (/\d/.test(v)) score++
  if (/[^A-Za-z0-9]/.test(v)) score++
  if (score <= 2) return { label: 'fraca', value: 33, color: 'error' as const }
  if (score <= 3) return { label: 'razoável', value: 66, color: 'warning' as const }
  return { label: 'boa', value: 100, color: 'success' as const }
})
</script>

<template>
  <div class="space-y-1.5">
    <UInput
      v-model="model"
      :type="visible ? 'text' : 'password'"
      :autocomplete="props.autocomplete"
      :placeholder="props.placeholder"
      icon="i-lucide-lock"
      size="lg"
      class="w-full"
      :ui="{ trailing: 'pe-1' }"
    >
      <template #trailing>
        <UButton
          color="neutral"
          variant="link"
          size="sm"
          :icon="visible ? 'i-lucide-eye-off' : 'i-lucide-eye'"
          :aria-label="visible ? 'Ocultar senha' : 'Mostrar senha'"
          :aria-pressed="visible"
          @click="visible = !visible"
        />
      </template>
    </UInput>
    <div
      v-if="props.showStrength && strength"
      class="flex items-center gap-2"
      aria-live="polite"
    >
      <UProgress
        :model-value="strength.value"
        :color="strength.color"
        size="xs"
        class="flex-1"
      />
      <span class="text-[11px] text-muted">Força: {{ strength.label }}</span>
    </div>
  </div>
</template>
