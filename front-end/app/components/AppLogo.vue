<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 28 })
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-md bg-inverted text-inverted"
    :style="{ width: `${size}px`, height: `${size}px` }"
    aria-hidden="true"
  >
    <span
      class="num font-semibold leading-none"
      :style="{ fontSize: `${Math.round(size * 0.43)}px` }"
    >cf</span>
  </span>
</template>
