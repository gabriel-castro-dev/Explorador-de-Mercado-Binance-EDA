<script setup lang="ts">
/**
 * Início (home de insights — Design.md §5). Shim permanente: deep links antigos
 * e o cookie de redirect pós-login apontavam para `/?symbol=…` quando o gráfico
 * morava aqui — esses caem direto em /graficos com a mesma query.
 */
const route = useRoute()

if (route.query.symbol) {
  await navigateTo({ path: '/graficos', query: route.query }, { replace: true })
}

useHead({ title: 'Início · crypto forecasting' })
</script>

<template>
  <div class="space-y-4">
    <h1 class="sr-only">
      Início
    </h1>
    <!-- Conteúdo do Início entra na fase 5b (insights + leitura do dia). -->
  </div>
</template>
