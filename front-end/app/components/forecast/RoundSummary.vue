<script setup lang="ts">
import type { ForecastRound } from '~/types/forecast'
import { splitReading } from '~/utils/insights'

/**
 * Resumo da rodada (Design.md §11.1): texto aberto, **sem card**.
 * Versão, MAE e acerto de direção vivem no `RoundFacts` do cabeçalho da página.
 */
const props = defineProps<{ round: ForecastRound | null }>()

const parts = computed(() => splitReading(props.round?.narrative))
</script>

<template>
  <div>
    <p
      v-reveal="{ y: 18 }"
      class="eyebrow text-[var(--cf-electric)]"
    >
      RESUMO DA RODADA
    </p>

    <template v-if="props.round && parts">
      <h2
        v-if="parts.headline"
        v-reveal="{ delay: 90, y: 28 }"
        class="cf-display mt-5 uppercase"
      >
        {{ parts.headline }}
      </h2>
      <p
        v-if="parts.body"
        v-reveal="{ delay: 170, y: 22 }"
        class="cf-body mt-7"
      >
        {{ parts.body }}
      </p>
    </template>

    <template v-else>
      <h2
        v-reveal="{ delay: 90, y: 28 }"
        class="cf-h2 mt-5"
      >
        O modelo ainda não publicou previsões para este ativo.
      </h2>
      <p
        v-reveal="{ delay: 170, y: 22 }"
        class="cf-body mt-6"
      >
        A primeira rodada publica os horizontes diário, semanal, mensal e anual dos
        20 ativos rastreados, com a média de erro e o acerto de direção medidos no
        backtesting. Até lá, nenhum número é exibido aqui.
      </p>
    </template>
  </div>
</template>
