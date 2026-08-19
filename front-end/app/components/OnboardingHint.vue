<script setup lang="ts">
/** Dica de primeiro acesso (ux-spec §4.5): dialog não modal; Esc fecha; foco não é roubado. */
const props = defineProps<{ symbol: string, tf: string }>()
const emit = defineEmits<{ (e: 'dismiss', permanent: boolean): void }>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('dismiss', false)
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div
    role="dialog"
    aria-labelledby="onboarding-title"
    class="rounded-lg border border-primary/40 bg-elevated p-4 shadow-[0_8px_24px_rgba(0,0,0,.10)] dark:shadow-[0_8px_24px_rgba(0,0,0,.45)]"
  >
    <div class="flex items-start gap-2">
      <UIcon
        name="i-lucide-sparkles"
        class="mt-0.5 size-4 text-primary"
      />
      <div class="flex-1">
        <h3
          id="onboarding-title"
          class="text-[14px] font-semibold text-highlighted"
        >
          Seu primeiro snapshot
        </h3>
        <p class="mt-1 text-[13px] text-muted">
          Abrimos o <span
            class="num text-default"
            translate="no"
          >{{ props.symbol }}</span> em {{ props.tf }}. Escolha outro ativo no seletor ou ligue indicadores no painel ao lado — suas escolhas ficam salvas neste navegador.
        </p>
        <div class="mt-3 flex items-center gap-2">
          <UButton
            size="xs"
            label="Entendi"
            @click="emit('dismiss', true)"
          />
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            label="Não mostrar de novo"
            @click="emit('dismiss', true)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
