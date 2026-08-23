<script setup lang="ts">
import type { DropdownMenuItem, NavigationMenuItem } from '@nuxt/ui'

const route = useRoute()
const user = useSupabaseUser()
const { signOut } = useAuthActions()

const email = computed(() => (user.value?.email as string | undefined) ?? '')
const initials = computed(() => email.value.slice(0, 2).toUpperCase() || '··')

const navItems = computed<NavigationMenuItem[]>(() => [
  { label: 'Início', icon: 'i-lucide-house', to: '/', active: route.path === '/' },
  { label: 'Gráficos', icon: 'i-lucide-chart-candlestick', to: '/graficos', active: route.path.startsWith('/graficos') },
  { label: 'Previsões', icon: 'i-lucide-sparkles', to: '/previsoes', active: route.path.startsWith('/previsoes') },
  { label: 'Mercado', icon: 'i-lucide-table-2', to: '/mercado', active: route.path.startsWith('/mercado') },
])

const accountItems = computed<DropdownMenuItem[][]>(() => [
  [{ label: email.value || 'Conta', icon: 'i-lucide-user', disabled: true }],
  [{ label: 'Preferências', icon: 'i-lucide-settings-2', to: '/preferencias' }],
  [{ label: 'Sair', icon: 'i-lucide-log-out', onSelect: () => void signOut() }],
])

const mobileNav = computed(() => [
  { label: 'Início', icon: 'i-lucide-house', to: '/', active: route.path === '/' },
  { label: 'Gráficos', icon: 'i-lucide-chart-candlestick', to: '/graficos', active: route.path.startsWith('/graficos') },
  { label: 'Previsões', icon: 'i-lucide-sparkles', to: '/previsoes', active: route.path.startsWith('/previsoes') },
  { label: 'Mercado', icon: 'i-lucide-table-2', to: '/mercado', active: route.path.startsWith('/mercado') },
])
</script>

<template>
  <div class="flex min-h-dvh flex-col pb-[calc(56px+env(safe-area-inset-bottom))] md:pb-0">
    <UHeader
      :toggle="false"
      :ui="{ root: 'h-[58px] border-b border-[var(--cf-border-muted)] bg-[rgba(6,11,22,.86)] backdrop-blur-[14px]', container: 'max-w-[1440px] h-[58px] gap-4', left: 'min-w-0' }"
    >
      <template #left>
        <NuxtLink
          to="/"
          class="flex items-center gap-2.5 rounded-md"
          aria-label="crypto forecasting — início"
        >
          <AppLogo />
          <span class="hidden text-[15px] font-semibold text-highlighted sm:inline">crypto forecasting</span>
        </NuxtLink>
        <UNavigationMenu
          :items="navItems"
          class="ml-4 hidden md:flex"
          aria-label="Principal"
          :ui="{ link: 'text-[13px]' }"
        />
      </template>

      <template #right>
        <UDropdownMenu
          :items="accountItems"
          :content="{ align: 'end' }"
          :ui="{ content: 'w-56' }"
        >
          <UButton
            color="neutral"
            variant="ghost"
            trailing-icon="i-lucide-chevron-down"
            aria-label="Conta"
            class="max-w-[180px]"
          >
            <UAvatar
              :text="initials"
              size="2xs"
              class="bg-primary-soft text-primary num"
            />
            <span class="hidden truncate text-[13px] sm:inline">{{ email || 'Conta' }}</span>
          </UButton>
        </UDropdownMenu>
      </template>
    </UHeader>

    <main class="mx-auto w-full max-w-[1440px] flex-1 px-4 py-4 md:px-6">
      <slot />
    </main>

    <!-- Barra inferior (mobile) — Início · Gráficos · Previsões · Mercado -->
    <nav
      class="fixed inset-x-0 bottom-0 z-40 flex border-t border-[var(--cf-border-muted)] bg-[rgba(6,11,22,.92)] backdrop-blur-[14px] md:hidden"
      style="padding-bottom: max(8px, env(safe-area-inset-bottom))"
      aria-label="Principal (mobile)"
    >
      <NuxtLink
        v-for="item in mobileNav"
        :key="item.to"
        :to="item.to"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px]"
        :class="item.active ? 'text-primary' : 'text-muted'"
        :aria-current="item.active ? 'page' : undefined"
      >
        <UIcon
          :name="item.icon"
          class="size-5"
        />{{ item.label }}
      </NuxtLink>
    </nav>
  </div>
</template>
