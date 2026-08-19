<script setup lang="ts">
import type { FeatureRow } from '~/types/api'
import type { useIndicatorPrefs } from '~/composables/useIndicatorPrefs'
import { INDICATOR_DEFS, type IndicatorKey } from '~/utils/constants'
import { warmupInfo } from '~/utils/chart-mapping'

const props = withDefaults(defineProps<{
  controller: ReturnType<typeof useIndicatorPrefs>
  features: readonly FeatureRow[]
  featuresStatus?: 'idle' | 'pending' | 'success' | 'error'
  /** Drawer mobile: itens com switch de 44 px. */
  variant?: 'aside' | 'drawer'
  highlightKey?: IndicatorKey | null
}>(), { variant: 'aside', featuresStatus: 'idle', highlightKey: null })

const emit = defineEmits<{ (e: 'retry-features'): void }>()

const colorMode = useColorMode()
const mode = computed<'light' | 'dark'>(() => (colorMode.value === 'dark' ? 'dark' : 'light'))
const toast = useToast()

const groups = [
  { key: 'price', label: 'Sobre o preço', defs: INDICATOR_DEFS.filter(d => d.group === 'price') },
  { key: 'below', label: 'Painéis abaixo', defs: INDICATOR_DEFS.filter(d => d.group === 'below') },
] as const

/** Nota de warm-up por indicador: só quando a janela atual ainda não tem valor. */
function warmupFor(key: IndicatorKey): string | null {
  const def = INDICATOR_DEFS.find(d => d.key === key)
  const field = def?.fields[0]
  if (!def || !field || !props.features.length) return null
  const info = warmupInfo(props.features, field, def.window)
  return info.hasAnyValue ? null : 'warm-up'
}

const featuresEmpty = computed(() => props.featuresStatus === 'success' && props.features.length === 0)

function onClearAll() {
  const snapshot = props.controller.clearAll()
  toast.add({
    title: 'Indicadores desligados.',
    color: 'neutral',
    duration: 5000,
    actions: [{ label: 'Desfazer', variant: 'outline', color: 'neutral', onClick: () => props.controller.restore(snapshot) }],
  })
}

function onRestore() {
  props.controller.restoreDefaults()
  toast.add({ title: 'Indicadores restaurados ao padrão.', color: 'neutral', icon: 'i-lucide-rotate-ccw' })
}
</script>

<template>
  <div
    class="flex h-full flex-col"
    aria-label="Indicadores"
  >
    <div class="flex items-baseline justify-between gap-2 px-4 pt-3 pb-2">
      <h2 class="text-[14px] font-semibold text-highlighted">
        Indicadores
      </h2>
      <span class="text-[11px] text-dimmed">persistem no navegador</span>
    </div>

    <div class="flex-1 overflow-y-auto px-4 pb-3">
      <p
        v-if="props.featuresStatus === 'error'"
        class="mb-3 rounded-md border border-default bg-muted px-2.5 py-2 text-[12px] text-muted"
        role="alert"
      >
        Indicadores não carregaram.
        <UButton
          variant="link"
          size="xs"
          class="p-0"
          label="Tentar novamente"
          @click="emit('retry-features')"
        />
      </p>
      <p
        v-else-if="featuresEmpty"
        class="mb-3 rounded-md border border-default bg-muted px-2.5 py-2 text-[12px] text-muted"
        role="status"
      >
        Indicadores indisponíveis para este ativo/timeframe.
      </p>

      <fieldset
        v-for="group in groups"
        :key="group.key"
        class="mb-4"
      >
        <legend class="eyebrow mb-1.5 text-dimmed">
          {{ group.label }}
        </legend>
        <ul class="space-y-0.5">
          <li
            v-for="def in group.defs"
            :key="def.key"
            class="rounded-md"
            :class="props.highlightKey === def.key ? 'outline-2 outline-offset-2 outline-primary' : ''"
          >
            <label
              class="flex cursor-pointer items-center gap-2.5 rounded-md px-1.5 py-1.5 hover:bg-muted"
              :class="props.variant === 'drawer' ? 'min-h-11' : 'min-h-8'"
              :title="def.title"
            >
              <USwitch
                v-if="props.variant === 'drawer'"
                :model-value="props.controller.prefs.value[def.key]"
                size="md"
                :aria-label="def.label"
                @update:model-value="(v: boolean) => props.controller.toggle(def.key, v)"
              />
              <UCheckbox
                v-else
                :model-value="props.controller.prefs.value[def.key]"
                :aria-label="def.label"
                @update:model-value="(v: boolean | 'indeterminate') => props.controller.toggle(def.key, v === true)"
              />
              <ChartSwatch
                :color="def.color[mode]"
                :style-name="def.lineStyle"
                :kind="def.pane === 'volume' ? 'bars' : 'line'"
                :width="18"
              />
              <span class="flex-1 text-[13px] text-default">{{ def.label }}</span>
              <span
                v-if="warmupFor(def.key)"
                class="num text-[11px] text-dimmed"
              >{{ warmupFor(def.key) }}</span>
            </label>
          </li>
        </ul>
      </fieldset>
    </div>

    <div class="border-t border-default px-4 py-3">
      <p class="flex items-start gap-1.5 text-[12px] text-muted">
        <UIcon
          name="i-lucide-info"
          class="mt-0.5 size-3.5 shrink-0"
        />
        <span>Linhas começam só depois da janela de cálculo (warm-up). Não é erro.</span>
      </p>
      <div class="mt-2 flex items-center gap-2">
        <UButton
          variant="ghost"
          color="neutral"
          size="xs"
          label="Restaurar padrão"
          @click="onRestore"
        />
        <UButton
          variant="ghost"
          color="neutral"
          size="xs"
          label="Limpar tudo"
          @click="onClearAll"
        />
      </div>
    </div>
  </div>
</template>
