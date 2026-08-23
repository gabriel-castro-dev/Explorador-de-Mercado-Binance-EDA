<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import { MAIN_NAV, isNavActive } from '~/utils/nav'

/**
 * Header fino e integrado ao fundo, com uma única hairline inferior (Design.md §6.1).
 * Navegação sem pills: item ativo em azul elétrico com sublinhado que cresce por scaleX.
 */
const route = useRoute()
const { signOut } = useAuthActions()
const { firstName, email } = useAccountIdentity()

const accountItems = computed<DropdownMenuItem[][]>(() => [
  [{ label: email.value || 'Conta', icon: 'i-lucide-user', type: 'label' as const }],
  [{ label: 'Preferências', icon: 'i-lucide-settings-2', to: '/preferencias' }],
  [{ label: 'Sair', icon: 'i-lucide-log-out', onSelect: () => void signOut() }],
])
</script>

<template>
  <header
    class="cf-hairline-b sticky top-0 z-50"
    style="background: rgba(5, 8, 17, 0.72); backdrop-filter: blur(16px)"
  >
    <div class="cf-shell cf-gutter grid h-(--cf-header-h) grid-cols-[auto_1fr_auto] items-center gap-4">
      <NuxtLink
        to="/"
        class="rounded-sm"
        aria-label="CRYPTO FORECASTING — início"
      >
        <AppBrand
          size="md"
          responsive
        />
      </NuxtLink>

      <nav
        class="hidden justify-center gap-8 self-stretch md:flex lg:gap-11"
        aria-label="Principal"
      >
        <NuxtLink
          v-for="item in MAIN_NAV"
          :key="item.to"
          :to="item.to"
          class="cf-navlink eyebrow relative flex items-center rounded-sm"
          :class="isNavActive(item, route.path) ? 'text-[var(--cf-electric)]' : 'text-muted hover:text-default'"
          :aria-current="isNavActive(item, route.path) ? 'page' : undefined"
        >
          {{ item.label }}
        </NuxtLink>
      </nav>

      <UDropdownMenu
        :items="accountItems"
        :content="{ align: 'end' }"
        :ui="{ content: 'w-60' }"
      >
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-circle-user-round"
          trailing-icon="i-lucide-chevron-down"
          class="min-h-9 max-w-[200px] text-[14px]"
          :aria-label="`Conta de ${firstName}`"
        >
          <span class="hidden truncate sm:inline">{{ firstName }}</span>
        </UButton>
      </UDropdownMenu>
    </div>
  </header>
</template>
