<script setup lang="ts">
import type { ForecastRound } from '~/types/forecast'
import { EM_DASH, formatNumber } from '~/utils/format'

/**
 * Versão, MAE e acerto de direção em faixa tipográfica com hairlines verticais
 * (Design.md §11.1) — sem pills. Sem rodada publicada, tudo é `—`.
 */
const props = defineProps<{ round: ForecastRound | null }>()

const facts = computed(() => {
  const r = props.round
  return [
    { term: 'Modelo', value: r ? `${r.model.toUpperCase()} · ${r.version} · ${r.status.toUpperCase()}` : `MODELO ${EM_DASH}` },
    // MAE do log-retorno em 1 dia, em % — a API não tem MAE em preço por símbolo global.
    { term: 'Erro médio absoluto', value: r?.maePercent == null ? `MAE ${EM_DASH}` : `MAE ${formatNumber(r.maePercent, 1)} %` },
    { term: 'Acerto de direção', value: r?.directionAccuracy == null ? `DIREÇÃO ${EM_DASH}` : `DIREÇÃO ${formatNumber(r.directionAccuracy, 0)} %` },
  ]
})
</script>

<template>
  <dl class="flex flex-wrap items-center">
    <div
      v-for="(fact, i) in facts"
      :key="fact.term"
      class="num py-1 text-[12px] tracking-[0.06em] text-muted"
      :class="i > 0 ? 'ms-4 border-s border-[var(--cf-hairline)] ps-4 lg:ms-6 lg:ps-6' : ''"
    >
      <dt class="sr-only">
        {{ fact.term }}
      </dt>
      <dd>{{ fact.value }}</dd>
    </div>
  </dl>
</template>
