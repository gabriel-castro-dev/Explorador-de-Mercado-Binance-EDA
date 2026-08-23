<script setup lang="ts">
/**
 * A marca aparece SEMPRE como CRYPTO FORECASTING, em caixa alta (Design.md §2.1).
 * No mobile a segunda palavra pode sumir por largura, mas o nome acessível continua
 * completo — daí o par `aria-hidden` + `sr-only`.
 */
const props = withDefaults(defineProps<{
  /** `sm` header mobile · `md` header desktop · `lg` telas de autenticação. */
  size?: 'sm' | 'md' | 'lg'
  /** Some com "FORECASTING" abaixo de 380px (header apertado). */
  responsive?: boolean
}>(), { size: 'md', responsive: false })

const sizeClass = computed(() => ({
  sm: 'text-[12px] tracking-[0.18em]',
  md: 'text-[13px] tracking-[0.2em]',
  lg: 'text-[14px] tracking-[0.24em]',
}[props.size]))
</script>

<template>
  <span
    class="font-medium whitespace-nowrap text-hi"
    :class="sizeClass"
  >
    <span
      aria-hidden="true"
      class="inline-flex items-baseline gap-[0.45em]"
    >
      <span>CRYPTO</span>
      <span :class="props.responsive ? 'hidden min-[380px]:inline' : ''">FORECASTING</span>
    </span>
    <span class="sr-only">CRYPTO FORECASTING</span>
  </span>
</template>
