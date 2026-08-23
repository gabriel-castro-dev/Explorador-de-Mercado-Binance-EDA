<script setup lang="ts">
import type { FeatureRow } from '~/types/api'
import type { useIndicatorPrefs } from '~/composables/useIndicatorPrefs'
import type { AsyncStatus } from '~/utils/async-state'
import { INDICATOR_DEFS, type IndicatorKey } from '~/utils/constants'
import { warmupInfo } from '~/utils/chart-mapping'

/**
 * Dock funcional de indicadores (Design.md §10 e §5.1). É uma das poucas
 * superfícies delimitadas do sistema — existe porque o espaço exige um painel,
 * não porque a informação precise de moldura.
 */
const props = withDefaults(defineProps<{
  controller: ReturnType<typeof useIndicatorPrefs>
  features: readonly FeatureRow[]
  featuresStatus?: AsyncStatus
  /** `drawer` (mobile) usa switches de 44 px; `dock` usa checkboxes. */
  variant?: 'dock' | 'drawer'
  /** Grupo "Modelo": cenários melhor/base/pior (undefined = grupo oculto). */
  scenario?: boolean
}>(), { variant: 'dock', featuresStatus: 'idle', scenario: undefined })

const emit = defineEmits<{ (e: 'retry-features'): void, (e: 'toggle-scenario', value: boolean): void }>()

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
  return warmupInfo(props.features, field, def.window).hasAnyValue ? null : 'warm-up'
}

const featuresEmpty = computed(() => props.featuresStatus === 'success' && props.features.length === 0)
const rowHeight = computed(() => (props.variant === 'drawer' ? 'min-h-11' : 'min-h-9'))

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
  <div class="flex h-full flex-col">
    <div
      v-if="props.variant === 'dock'"
      class="cf-hairline-b flex items-baseline justify-between gap-2 px-4 pt-4 pb-3"
    >
      <h2 class="eyebrow text-muted">
        Indicadores
      </h2>
      <span class="text-[11px] text-dimmed">persistem no navegador</span>
    </div>

    <div
      class="flex-1 overflow-y-auto px-4 py-4"
      :class="props.variant === 'drawer' ? 'px-0' : ''"
    >
      <p
        v-if="props.featuresStatus === 'error'"
        class="mb-4 flex flex-wrap items-center gap-x-2 gap-y-1 text-[13px] text-muted"
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
        class="mb-4 text-[13px] text-muted"
        role="status"
      >
        Indicadores indisponíveis para este ativo/timeframe.
      </p>

      <fieldset
        v-for="group in groups"
        :key="group.key"
        class="mb-5"
      >
        <legend class="eyebrow mb-2 text-dimmed">
          {{ group.label }}
        </legend>
        <ul>
          <li
            v-for="def in group.defs"
            :key="def.key"
          >
            <label
              class="flex cursor-pointer items-center gap-3 rounded-md px-1.5 transition-colors hover:bg-[var(--cf-electric)]/6"
              :class="rowHeight"
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
                :color="def.color"
                :style-name="def.lineStyle"
                :kind="def.pane === 'volume' ? 'bars' : 'line'"
                :width="18"
              />
              <span class="flex-1 text-[14px] text-default">{{ def.label }}</span>
              <span
                v-if="warmupFor(def.key)"
                class="num text-[11px] text-dimmed"
              >{{ warmupFor(def.key) }}</span>
            </label>
          </li>
        </ul>
      </fieldset>

      <!-- Grupo Modelo: o ciano marca o que vem da IA (Design.md §4.2) -->
      <fieldset
        v-if="props.scenario !== undefined"
        class="mb-5"
      >
        <legend class="eyebrow mb-2 text-dimmed">
          Modelo
        </legend>
        <label
          class="flex cursor-pointer items-center gap-3 rounded-md px-1.5 transition-colors hover:bg-[var(--cf-electric)]/6"
          :class="rowHeight"
          title="Cenários de melhor caso, base e pior caso depois da linha de corte"
        >
          <USwitch
            v-if="props.variant === 'drawer'"
            :model-value="props.scenario"
            size="md"
            aria-label="Cenários (melhor/base/pior)"
            @update:model-value="(v: boolean) => emit('toggle-scenario', v)"
          />
          <UCheckbox
            v-else
            :model-value="props.scenario"
            aria-label="Cenários (melhor/base/pior)"
            @update:model-value="(v: boolean | 'indeterminate') => emit('toggle-scenario', v === true)"
          />
          <span class="flex-1 text-[14px] text-default">Cenários</span>
          <span class="num text-[10px] tracking-[0.1em] text-ai">IA · v0</span>
        </label>
      </fieldset>
    </div>

    <div
      class="cf-hairline-t px-4 py-4"
      :class="props.variant === 'drawer' ? 'px-0' : ''"
    >
      <p class="flex items-start gap-2 text-[13px] text-muted">
        <UIcon
          name="i-lucide-info"
          class="mt-0.5 size-3.5 shrink-0"
          aria-hidden="true"
        />
        <span>Linhas começam só depois da janela de cálculo (warm-up). Não é erro.</span>
      </p>
      <div class="mt-3 flex flex-wrap items-center gap-2">
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
