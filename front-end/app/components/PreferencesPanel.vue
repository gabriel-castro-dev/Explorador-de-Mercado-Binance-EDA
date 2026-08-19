<script setup lang="ts">
const hollow = useHollowCandles()
</script>

<template>
  <div class="space-y-4">
    <USwitch
      v-model="hollow"
      label="Velas de alta vazadas"
      description="Alternativa para daltonismo (deutan): alta com corpo transparente e borda; baixa preenchida."
    />
    <p class="text-[12px] text-muted">
      Os indicadores ligados também ficam salvos neste navegador (painel Indicadores → Restaurar padrão).
    </p>
  </div>
</template>
