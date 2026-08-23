<script setup lang="ts">
/**
 * Paisagem de dados da abertura (Design.md §1.2, mockup 02): curvas, hastes e
 * partículas ascendentes no canto inferior direito. É iluminação atmosférica —
 * nunca contorno de painel — e é desenhada por `stroke-dashoffset` ao entrar.
 */
const host = ref<HTMLElement | null>(null)
const entered = useEnterOnce(host, 0.1)

const CURVES = [
  { d: 'M0 300 C 120 296 190 262 300 236 C 410 210 470 150 580 120 C 680 93 740 86 800 84', width: 1.5, opacity: 0.62, delay: 120 },
  { d: 'M0 336 C 130 334 200 312 320 288 C 440 264 500 214 620 186 C 710 165 760 158 800 156', width: 1.1, opacity: 0.34, delay: 300 },
  { d: 'M0 372 C 140 372 220 356 340 336 C 460 316 520 276 640 250 C 720 233 770 228 800 226', width: 0.9, opacity: 0.18, delay: 460 },
] as const

/** Hastes verticais com o ponto no topo, como no mockup. */
const STEMS = [
  { x: 236, y: 250, h: 96 },
  { x: 386, y: 196, h: 128 },
  { x: 536, y: 140, h: 150 },
  { x: 686, y: 104, h: 168 },
] as const

const DUST = [
  { cx: 120, cy: 330, r: 1.4 }, { cx: 300, cy: 268, r: 1 }, { cx: 452, cy: 214, r: 1.6 },
  { cx: 610, cy: 178, r: 1 }, { cx: 742, cy: 132, r: 1.3 }, { cx: 196, cy: 356, r: 1 },
  { cx: 520, cy: 296, r: 1.2 }, { cx: 668, cy: 220, r: 1 },
] as const
</script>

<template>
  <div
    ref="host"
    class="pointer-events-none absolute right-0 bottom-0 -z-10 hidden h-[62%] w-[68%] md:block"
    aria-hidden="true"
  >
    <svg
      class="size-full"
      viewBox="0 0 800 400"
      preserveAspectRatio="xMaxYMax slice"
      fill="none"
    >
      <path
        v-for="(curve, i) in CURVES"
        :key="`c-${i}`"
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
          transition: `stroke-dashoffset 1500ms var(--cf-ease-section) ${curve.delay}ms`,
        }"
      />

      <g
        v-for="(stem, i) in STEMS"
        :key="`s-${i}`"
        :style="{ opacity: entered ? 1 : 0, transition: `opacity 600ms var(--cf-ease-micro) ${900 + i * 120}ms` }"
      >
        <line
          :x1="stem.x"
          :y1="stem.y"
          :x2="stem.x"
          :y2="stem.y + stem.h"
          stroke="var(--cf-cyan)"
          stroke-opacity="0.22"
          stroke-width="1"
          vector-effect="non-scaling-stroke"
        />
        <circle
          :cx="stem.x"
          :cy="stem.y"
          r="3.2"
          fill="var(--cf-cyan)"
          fill-opacity="0.9"
        />
      </g>

      <circle
        v-for="(dot, i) in DUST"
        :key="`d-${i}`"
        :cx="dot.cx"
        :cy="dot.cy"
        :r="dot.r"
        fill="var(--cf-ice)"
        fill-opacity="0.34"
        :style="{ opacity: entered ? 1 : 0, transition: `opacity 800ms var(--cf-ease-micro) ${1100 + i * 70}ms` }"
      />
    </svg>
  </div>
</template>
