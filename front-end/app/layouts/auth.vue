<script setup lang="ts">
/**
 * Ambiente de autenticação (Design.md §8): marca pequena no topo esquerdo, margem
 * ampla, torus à esquerda e formulário no terço direito — integrado ao fundo, sem
 * card externo. O Login é imersivo; as demais telas usam o torus estático.
 */
const route = useRoute()
const variant = computed<'immersive' | 'quiet'>(() => (route.path === '/login' ? 'immersive' : 'quiet'))
</script>

<template>
  <div class="relative min-h-dvh overflow-hidden">
    <AuthBackdrop :variant="variant" />

    <div class="cf-gutter relative z-10 flex min-h-dvh flex-col py-7 lg:py-9">
      <NuxtLink
        to="/login"
        class="self-start rounded-sm"
        aria-label="CRYPTO FORECASTING — entrar"
      >
        <AppBrand size="lg" />
      </NuxtLink>

      <div class="flex flex-1 items-center justify-center py-10 lg:justify-end lg:py-6">
        <div class="w-full max-w-[420px] lg:me-[3vw] xl:me-[5vw]">
          <slot />
        </div>
      </div>

      <p class="num text-[11px] tracking-[0.02em] text-dimmed lg:text-end">
        Dados da Binance · snapshots diários · horários em UTC
      </p>
    </div>
  </div>
</template>
