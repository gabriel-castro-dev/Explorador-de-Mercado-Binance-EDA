<script setup lang="ts">
import type { DropdownMenuItem, NavigationMenuItem } from '@nuxt/ui'

const route = useRoute()
const user = useSupabaseUser()
const { signOut } = useAuthActions()
const drawerOpen = useIndicatorsDrawer()
const prefsOpen = ref(false)

const email = computed(() => (user.value?.email as string | undefined) ?? '')
const initials = computed(() => email.value.slice(0, 2).toUpperCase() || '··')

const navItems = computed<NavigationMenuItem[]>(() => [
  { label: 'Dashboard', icon: 'i-lucide-trending-up', to: '/', active: route.path === '/' },
  { label: 'Mercado', icon: 'i-lucide-table-2', to: '/mercado', active: route.path.startsWith('/mercado') },
  { label: 'Previsões', icon: 'i-lucide-sparkles', disabled: true, badge: { label: 'EM BREVE', variant: 'outline', color: 'neutral', class: 'eyebrow' }, title: 'Previsões do modelo — em breve' },
])

const accountItems = computed<DropdownMenuItem[][]>(() => [
  [{ label: email.value || 'Conta', icon: 'i-lucide-user', disabled: true }],
  [{ label: 'Preferências', icon: 'i-lucide-settings-2', onSelect: () => { prefsOpen.value = true } }],
  [{ label: 'Sair', icon: 'i-lucide-log-out', onSelect: () => void signOut() }],
])

const isDashboard = computed(() => route.path === '/')
</script>

<template>
  <div class="flex min-h-dvh flex-col pb-[calc(56px+env(safe-area-inset-bottom))] md:pb-0">
    <UHeader
      :toggle="false"
      :ui="{ root: 'h-14 border-b border-default bg-elevated/95 backdrop-blur', container: 'max-w-[1440px] h-14 gap-4', left: 'min-w-0' }"
    >
      <template #left>
        <NuxtLink
          to="/"
          class="flex items-center gap-2.5 rounded-md"
          aria-label="crypto forecasting — dashboard"
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
        <UTooltip text="Alternar tema claro/escuro">
          <UColorModeButton
            color="neutral"
            variant="ghost"
            aria-label="Alternar tema claro/escuro"
          />
        </UTooltip>
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

    <!-- Barra inferior (mobile) — ux-spec §2/§11 -->
    <nav
      class="fixed inset-x-0 bottom-0 z-40 flex border-t border-default bg-elevated md:hidden"
      style="padding-bottom: max(8px, env(safe-area-inset-bottom))"
      aria-label="Principal (mobile)"
    >
      <NuxtLink
        to="/"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px]"
        :class="isDashboard ? 'text-primary' : 'text-muted'"
        :aria-current="isDashboard ? 'page' : undefined"
      >
        <UIcon
          name="i-lucide-trending-up"
          class="size-5"
        />Dashboard
      </NuxtLink>
      <NuxtLink
        to="/mercado"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px]"
        :class="route.path.startsWith('/mercado') ? 'text-primary' : 'text-muted'"
        :aria-current="route.path.startsWith('/mercado') ? 'page' : undefined"
      >
        <UIcon
          name="i-lucide-table-2"
          class="size-5"
        />Mercado
      </NuxtLink>
      <button
        v-if="isDashboard"
        type="button"
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] text-muted"
        aria-haspopup="dialog"
        :aria-expanded="drawerOpen"
        @click="drawerOpen = true"
      >
        <UIcon
          name="i-lucide-sliders-horizontal"
          class="size-5"
        />Indicadores
      </button>
      <span
        v-else
        class="flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] text-dimmed"
        aria-disabled="true"
        title="Previsões — em breve"
      >
        <UIcon
          name="i-lucide-sparkles"
          class="size-5"
        />Previsões
      </span>
    </nav>

    <UModal
      v-model:open="prefsOpen"
      title="Preferências"
      description="Ajustes salvos neste navegador."
    >
      <template #body>
        <PreferencesPanel />
      </template>
    </UModal>
  </div>
</template>
