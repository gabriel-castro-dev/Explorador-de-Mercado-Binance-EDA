<script setup lang="ts">
/**
 * Lente editorial das mudanças desde o último acesso.
 *
 * A geometria é estrutural, não quantitativa: substitui a letra monumental sem
 * sugerir valores que a API ainda não fornece. A animação acontece uma única
 * vez quando o componente entra no viewport.
 */
const lens = useTemplateRef<HTMLElement>('lens')
const entered = useEnterOnce(lens, 0.1)
</script>

<template>
  <figure
    ref="lens"
    class="market-delta-lens"
    :class="{ 'is-entered': entered }"
    role="img"
    aria-label="Lente editorial das mudanças do mercado desde o seu último acesso"
  >
    <figcaption class="market-delta-lens__label">
      DESDE SEU ÚLTIMO ACESSO
    </figcaption>

    <svg
      class="market-delta-lens__graphic"
      viewBox="0 0 320 340"
      fill="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient
          id="delta-path-primary"
          x1="38"
          y1="188"
          x2="278"
          y2="86"
          gradientUnits="userSpaceOnUse"
        >
          <stop
            stop-color="var(--cf-electric)"
            stop-opacity="0.3"
          />
          <stop
            offset="0.72"
            stop-color="var(--cf-cyan)"
            stop-opacity="0.9"
          />
          <stop
            offset="1"
            stop-color="var(--cf-ice)"
          />
        </linearGradient>
        <linearGradient
          id="delta-path-secondary"
          x1="38"
          y1="190"
          x2="278"
          y2="250"
          gradientUnits="userSpaceOnUse"
        >
          <stop
            stop-color="var(--cf-electric)"
            stop-opacity="0.18"
          />
          <stop
            offset="1"
            stop-color="var(--cf-cyan)"
            stop-opacity="0.68"
          />
        </linearGradient>
        <radialGradient
          id="delta-focus"
          cx="0"
          cy="0"
          r="1"
          gradientTransform="translate(278 166) rotate(90) scale(28)"
        >
          <stop
            stop-color="var(--cf-cyan)"
            stop-opacity="0.28"
          />
          <stop
            offset="1"
            stop-color="var(--cf-cyan)"
            stop-opacity="0"
          />
        </radialGradient>
      </defs>

      <g class="market-delta-lens__time">
        <line
          x1="278"
          y1="55"
          x2="278"
          y2="292"
          stroke="var(--cf-ice)"
          stroke-opacity="0.2"
          vector-effect="non-scaling-stroke"
        />
        <text
          x="278"
          y="316"
          fill="var(--cf-text-dim)"
          font-size="9"
          letter-spacing="1.2"
          text-anchor="middle"
        >AGORA</text>
      </g>

      <path
        class="market-delta-lens__path market-delta-lens__path--upper"
        d="M38 188 C82 187 105 177 133 158 C169 133 201 92 278 78"
        pathLength="1"
        stroke="url(#delta-path-primary)"
        stroke-width="1.6"
        stroke-linecap="round"
        vector-effect="non-scaling-stroke"
      />
      <path
        class="market-delta-lens__path market-delta-lens__path--middle"
        d="M38 190 C86 190 113 185 145 174 C188 159 220 158 278 166"
        pathLength="1"
        stroke="var(--cf-cyan)"
        stroke-opacity="0.56"
        stroke-width="1.2"
        stroke-linecap="round"
        vector-effect="non-scaling-stroke"
      />
      <path
        class="market-delta-lens__path market-delta-lens__path--lower"
        d="M38 192 C85 194 111 203 145 220 C188 242 223 258 278 250"
        pathLength="1"
        stroke="url(#delta-path-secondary)"
        stroke-width="1"
        stroke-linecap="round"
        vector-effect="non-scaling-stroke"
      />
      <path
        class="market-delta-lens__path market-delta-lens__path--echo"
        d="M38 190 C91 191 121 181 154 163 C196 140 229 121 278 118"
        pathLength="1"
        stroke="var(--cf-ice)"
        stroke-opacity="0.12"
        stroke-width="0.8"
        stroke-dasharray="3 7"
        vector-effect="non-scaling-stroke"
      />

      <g class="market-delta-lens__origin">
        <circle
          cx="38"
          cy="190"
          r="3.5"
          fill="var(--cf-electric)"
        />
        <circle
          cx="38"
          cy="190"
          r="9"
          stroke="var(--cf-electric)"
          stroke-opacity="0.16"
        />
      </g>

      <g class="market-delta-lens__markers">
        <circle
          cx="133"
          cy="158"
          r="2.3"
          fill="var(--cf-cyan)"
          fill-opacity="0.78"
        />
        <circle
          cx="145"
          cy="174"
          r="2"
          fill="var(--cf-ice)"
          fill-opacity="0.62"
        />
        <circle
          cx="145"
          cy="220"
          r="1.8"
          fill="var(--cf-cyan)"
          fill-opacity="0.48"
        />
        <circle
          cx="221"
          cy="158"
          r="2.2"
          fill="var(--cf-cyan)"
          fill-opacity="0.68"
        />
        <circle
          cx="229"
          cy="121"
          r="1.7"
          fill="var(--cf-ice)"
          fill-opacity="0.44"
        />
      </g>

      <circle
        class="market-delta-lens__focus-halo"
        cx="278"
        cy="166"
        r="28"
        fill="url(#delta-focus)"
      />
      <circle
        class="market-delta-lens__focus"
        cx="278"
        cy="166"
        r="4"
        fill="var(--cf-ice)"
      />
      <circle
        class="market-delta-lens__focus-ring"
        cx="278"
        cy="166"
        r="9"
        stroke="var(--cf-cyan)"
        stroke-opacity="0.48"
      />
    </svg>
  </figure>
</template>

<style scoped>
.market-delta-lens {
  width: min(100%, 22rem);
  margin: 0;
  color: var(--cf-text-dim);
}

.market-delta-lens__label {
  font-size: 0.6875rem;
  line-height: 1.2;
  font-weight: 550;
  letter-spacing: 0.12em;
  color: var(--cf-text-dim);
}

.market-delta-lens__graphic {
  display: block;
  width: 100%;
  height: auto;
  margin-top: 0.75rem;
  overflow: visible;
}

.market-delta-lens__time {
  opacity: 0;
  transform: scaleY(0);
  transform-origin: 278px 292px;
  transition:
    opacity 500ms var(--cf-ease-micro),
    transform 650ms var(--cf-ease-section);
}

.market-delta-lens__path {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  transition: stroke-dashoffset 980ms var(--cf-ease-section);
}

.market-delta-lens__path--upper { transition-delay: 160ms; }
.market-delta-lens__path--middle { transition-delay: 240ms; }
.market-delta-lens__path--lower { transition-delay: 320ms; }
.market-delta-lens__path--echo { transition-delay: 400ms; }

.market-delta-lens__origin,
.market-delta-lens__markers,
.market-delta-lens__focus,
.market-delta-lens__focus-ring,
.market-delta-lens__focus-halo {
  opacity: 0;
  transition: opacity 240ms var(--cf-ease-micro);
}

.market-delta-lens__origin { transition-delay: 120ms; }
.market-delta-lens__markers { transition-delay: 720ms; }
.market-delta-lens__focus,
.market-delta-lens__focus-ring { transition-delay: 1030ms; }

.market-delta-lens.is-entered .market-delta-lens__time {
  opacity: 1;
  transform: scaleY(1);
}

.market-delta-lens.is-entered .market-delta-lens__path { stroke-dashoffset: 0; }

.market-delta-lens.is-entered .market-delta-lens__origin,
.market-delta-lens.is-entered .market-delta-lens__markers,
.market-delta-lens.is-entered .market-delta-lens__focus,
.market-delta-lens.is-entered .market-delta-lens__focus-ring { opacity: 1; }

.market-delta-lens.is-entered .market-delta-lens__focus-halo {
  animation: market-delta-focus 560ms var(--cf-ease-section) 1040ms both;
}

@keyframes market-delta-focus {
  0% {
    opacity: 0;
    transform: scale(0.62);
    transform-origin: 278px 166px;
  }

  52% {
    opacity: 1;
    transform: scale(1.14);
    transform-origin: 278px 166px;
  }

  100% {
    opacity: 0.52;
    transform: scale(1);
    transform-origin: 278px 166px;
  }
}

@media (max-width: 1023px) {
  .market-delta-lens { width: min(100%, 20rem); }
}

@media (prefers-reduced-motion: reduce) {
  .market-delta-lens__time {
    opacity: 1;
    transform: none;
  }

  .market-delta-lens__path { stroke-dashoffset: 0; }

  .market-delta-lens__origin,
  .market-delta-lens__markers,
  .market-delta-lens__focus,
  .market-delta-lens__focus-ring { opacity: 1; }

  .market-delta-lens__focus-halo {
    opacity: 0.52;
    animation: none;
  }
}
</style>
