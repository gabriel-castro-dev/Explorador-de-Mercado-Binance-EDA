<script setup lang="ts">
import { MAIN_NAV, isNavActive } from '~/utils/nav'

/** Barra inferior do mobile com safe area (Design.md §6.2). Alvo mínimo 44 px. */
const route = useRoute()
</script>

<template>
  <nav
    class="cf-hairline-t fixed inset-x-0 bottom-0 z-50 flex md:hidden"
    style="background: rgba(5, 8, 17, 0.92); backdrop-filter: blur(16px); padding-bottom: env(safe-area-inset-bottom)"
    aria-label="Principal"
  >
    <NuxtLink
      v-for="item in MAIN_NAV"
      :key="item.to"
      :to="item.to"
      class="relative flex min-h-[58px] flex-1 flex-col items-center justify-center gap-1"
      :class="isNavActive(item, route.path) ? 'text-[var(--cf-electric)]' : 'text-muted'"
      :aria-current="isNavActive(item, route.path) ? 'page' : undefined"
    >
      <span
        v-if="isNavActive(item, route.path)"
        class="absolute inset-x-5 top-0 h-[1.5px] bg-[var(--cf-electric)]"
        aria-hidden="true"
      />
      <UIcon
        :name="item.icon"
        class="size-[18px]"
        aria-hidden="true"
      />
      <span class="eyebrow text-[10px] tracking-[0.1em]">{{ item.label }}</span>
    </NuxtLink>
  </nav>
</template>
