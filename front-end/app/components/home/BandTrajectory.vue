<script setup lang="ts">
/**
 * Trajetória contínua que atravessa as três leituras (Design.md §9.2).
 * Desenhada por `stroke-dashoffset` quando entra no viewport; no mobile vira
 * um fio vertical de continuidade. Puramente atmosférica: aria-hidden.
 */
const host = ref<HTMLElement | null>(null)
const entered = useEnterOnce(host, 0.15)

/** `pathLength="1"` normaliza o comprimento: o dash funciona igual em qualquer viewBox. */
const CURVES = [
  { d: 'M0 262 C 150 262 210 150 340 138 C 470 126 520 196 660 200 C 800 204 850 118 980 104 C 1080 93 1140 128 1200 132', width: 1.3, opacity: 0.5, delay: 0 },
  { d: 'M0 318 C 170 318 230 248 360 244 C 500 240 540 300 690 296 C 830 292 890 214 1010 202 C 1100 193 1150 214 1200 216', width: 1, opacity: 0.28, delay: 180 },
] as const

const DOTS = [
  { cx: 112, cy: 268 },
  { cx: 660, cy: 200 },
  { cx: 1074, cy: 110 },
] as const
</script>

<template>
  <div
    ref="host"
    class="pointer-events-none absolute inset-0 -z-10"
    aria-hidden="true"
  >
    <svg
      class="hidden size-full md:block"
      viewBox="0 0 1200 400"
      preserveAspectRatio="none"
      fill="none"
    >
      <path
        v-for="(curve, i) in CURVES"
        :key="i"
        :d="curve.d"
        pathLength="1"
        stroke="var(--cf-cyan)"
        :stroke-width="curve.width"
        :stroke-opacity="curve.opacity"
        stroke-linecap="round"
        vector-effect="non-scaling-stroke"
        :style="{
          strokeDasharray: 1,
          strokeDashoffset: entered ? 0 : 1,
          transition: `stroke-dashoffset 1400ms var(--cf-ease-section) ${curve.delay}ms`,
        }"
      />
      <circle
        v-for="(dot, i) in DOTS"
        :key="`dot-${i}`"
        :cx="dot.cx"
        :cy="dot.cy"
        r="3.5"
        fill="var(--cf-cyan)"
        :style="{
          opacity: entered ? 0.85 : 0,
          transition: `opacity 500ms var(--cf-ease-micro) ${900 + i * 140}ms`,
        }"
      />
    </svg>

    <!-- Mobile: fio vertical de continuidade entre as faixas empilhadas. -->
    <span
      class="absolute inset-y-0 left-[9px] w-px md:hidden"
      style="background: linear-gradient(180deg, transparent, rgba(95, 196, 255, 0.28) 12%, rgba(95, 196, 255, 0.28) 88%, transparent)"
      :style="{ opacity: entered ? 1 : 0, transition: 'opacity 700ms var(--cf-ease-section)' }"
    />
  </div>
</template>
