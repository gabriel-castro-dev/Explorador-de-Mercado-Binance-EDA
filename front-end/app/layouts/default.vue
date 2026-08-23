<template>
  <div class="flex min-h-dvh flex-col">
    <a
      href="#conteudo"
      class="sr-only rounded-md bg-elevated px-4 py-2 text-[14px] text-hi focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[70]"
    >Ir para o conteúdo</a>

    <AppHeader />

    <main
      id="conteudo"
      class="flex-1 pb-[calc(var(--cf-tabbar-h)+8px)] md:pb-0"
    >
      <slot />
    </main>

    <AppTabBar />
  </div>
</template>
