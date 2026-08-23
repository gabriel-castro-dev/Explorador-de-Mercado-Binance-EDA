<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 28 })
</script>

<template>
  <!-- Logo real (fundo preto some sobre o navy via blend screen — Design.md §4). -->
  <img
    src="/crypto-forecasting-logo-v5.png"
    alt=""
    aria-hidden="true"
    class="inline-block shrink-0 select-none"
    :style="{ width: `${size}px`, height: `${size}px`, mixBlendMode: 'screen', objectFit: 'contain' }"
    draggable="false"
  >
</template>
