<template>
  <div class="flex min-h-dvh flex-col items-center justify-center px-4 py-10">
    <NuxtLink
      to="/login"
      class="mb-6 flex items-center gap-2.5 rounded-md"
      aria-label="crypto forecasting — início"
    >
      <AppLogo />
      <span class="text-[15px] font-semibold text-highlighted">crypto forecasting</span>
    </NuxtLink>

    <UCard
      class="w-full max-w-[400px] rounded-lg"
      :ui="{ body: 'p-7 sm:p-7' }"
    >
      <slot />
    </UCard>

    <p class="num mt-6 text-[11px] text-dimmed">
      Dados da Binance · snapshots diários · horários em UTC
    </p>
  </div>
</template>
