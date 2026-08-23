<script setup lang="ts">
import type { HorizonSummary } from '~/types/forecast'
import { HORIZONS } from '~/types/forecast'
import { EM_DASH, formatPercent } from '~/utils/format'

/**
 * Quatro arcos partindo de DADO OBSERVADO (Design.md §11.1): diário, semanal,
 * mensal e anual. A abertura crescente comunica o aumento da incerteza — é
 * geometria da estrutura, não um número previsto.
 *
 * Sem nenhuma variação publicada, os arcos **não são desenhados**: trajetória só
 * existe com dado real. Nesse caso a tela mostra a lista de horizontes com `—`.
 */
const props = defineProps<{ horizons: readonly HorizonSummary[] }>()

const host = ref<HTMLElement | null>(null)
const entered = useEnterOnce(host, 0.25)

const ORIGIN = { x: 92, y: 486 }
const END_X = 560
/** Alturas de chegada: quanto mais longe o horizonte, mais aberto o arco. */
const END_Y: Record<string, number> = { daily: 428, weekly: 316, monthly: 196, yearly: 62 }

const byKey = computed(() => new Map(props.horizons.map(h => [h.key, h])))
const hasAnyValue = computed(() => props.horizons.some(h => h.changePercent !== null))

const arcs = computed(() => HORIZONS.map((horizon, index) => {
  const endY = END_Y[horizon.key] ?? 300
  const rise = ORIGIN.y - endY
  return {
    key: horizon.key,
    label: horizon.label,
    value: byKey.value.get(horizon.key)?.changePercent ?? null,
    endY,
    d: `M ${ORIGIN.x} ${ORIGIN.y} C ${ORIGIN.x + 46} ${ORIGIN.y - rise * 0.64}, ${END_X - 210} ${endY}, ${END_X} ${endY}`,
    /** 900–1.200 ms com pequeno stagger entre horizontes. */
    duration: 980 + index * 60,
    delay: index * 110,
  }
}))

function toneClass(value: number | null) {
  if (value === null) return 'text-dimmed'
  return value < 0 ? 'text-down' : 'text-ai'
}
</script>

<template>
  <div ref="host">
    <!-- Desktop: arcos -->
    <svg
      v-if="hasAnyValue"
      class="hidden h-auto w-full md:block"
      viewBox="0 0 760 540"
      fill="none"
      role="img"
      aria-label="Projeção média por horizonte, partindo do último dado observado. Os valores estão listados ao lado de cada arco."
    >
      <!-- Elipses de fundo: profundidade atmosférica sob a origem -->
      <g
        aria-hidden="true"
        :style="{ opacity: entered ? 1 : 0, transition: 'opacity 900ms var(--cf-ease-section)' }"
      >
        <ellipse
          v-for="(r, i) in [80, 140, 205, 275]"
          :key="r"
          :cx="ORIGIN.x + 210"
          :cy="ORIGIN.y + 6"
          :rx="r"
          :ry="r * 0.22"
          stroke="var(--cf-cyan)"
          :stroke-opacity="0.13 - i * 0.025"
          stroke-width="1"
          stroke-dasharray="2 6"
        />
      </g>

      <g>
        <path
          v-for="arc in arcs"
          :key="arc.key"
          :d="arc.d"
          pathLength="1"
          stroke="var(--cf-cyan)"
          stroke-width="1.4"
          stroke-opacity="0.85"
          stroke-linecap="round"
          :style="{
            strokeDasharray: 1,
            strokeDashoffset: entered ? 0 : 1,
            transition: `stroke-dashoffset ${arc.duration}ms var(--cf-ease-section) ${arc.delay}ms`,
          }"
        />
      </g>

      <g aria-hidden="true">
        <template
          v-for="arc in arcs"
          :key="`label-${arc.key}`"
        >
          <line
            :x1="END_X"
            :y1="arc.endY"
            :x2="END_X + 74"
            :y2="arc.endY"
            stroke="var(--cf-cyan)"
            stroke-opacity="0.45"
            stroke-width="1"
            stroke-dasharray="2 5"
            :style="{ opacity: entered ? 1 : 0, transition: `opacity 400ms var(--cf-ease-micro) ${arc.delay + arc.duration}ms` }"
          />
          <circle
            :cx="END_X + 74"
            :cy="arc.endY"
            r="4.5"
            fill="var(--cf-cyan)"
            :style="{ opacity: entered ? 1 : 0, transition: `opacity 400ms var(--cf-ease-micro) ${arc.delay + arc.duration}ms` }"
          />
          <text
            :x="END_X + 90"
            :y="arc.endY - 8"
            class="cf-arc-label"
            :style="{ opacity: entered ? 1 : 0, transition: `opacity 450ms var(--cf-ease-micro) ${arc.delay + arc.duration + 80}ms` }"
          >{{ arc.label }}</text>
          <text
            :x="END_X + 90"
            :y="arc.endY + 20"
            class="cf-arc-value"
            :class="toneClass(arc.value)"
            :style="{ opacity: entered ? 1 : 0, transition: `opacity 450ms var(--cf-ease-micro) ${arc.delay + arc.duration + 140}ms` }"
          >{{ arc.value === null ? EM_DASH : formatPercent(arc.value, 1) }}</text>
        </template>

        <circle
          :cx="ORIGIN.x"
          :cy="ORIGIN.y"
          r="6"
          fill="var(--cf-cyan)"
        />
        <text
          :x="ORIGIN.x - 6"
          :y="ORIGIN.y + 30"
          class="cf-arc-label"
        >DADO OBSERVADO</text>
      </g>
    </svg>

    <!-- Mobile, e desktop sem rodada: lista de horizontes com hairlines -->
    <dl :class="hasAnyValue ? 'md:hidden' : ''">
      <div
        v-for="horizon in arcs"
        :key="`row-${horizon.key}`"
        class="cf-rule flex items-baseline justify-between gap-4 py-4"
      >
        <dt class="eyebrow text-muted">
          {{ horizon.label }}
        </dt>
        <dd
          class="num text-[17px]"
          :class="toneClass(horizon.value)"
        >
          {{ horizon.value === null ? EM_DASH : formatPercent(horizon.value, 1) }}
        </dd>
      </div>
      <p class="num mt-4 text-[11px] text-dimmed">
        Partindo do último dado observado · a incerteza cresce com o horizonte
      </p>
    </dl>
  </div>
</template>

<style scoped>
.cf-arc-label {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  fill: var(--cf-text-muted);
}

.cf-arc-value {
  font-family: var(--font-mono);
  font-size: 22px;
  font-variant-numeric: tabular-nums;
  fill: var(--cf-cyan);
}

.cf-arc-value.text-down {
  fill: var(--cf-down);
}

.cf-arc-value.text-dimmed {
  fill: var(--cf-text-dim);
}
</style>
