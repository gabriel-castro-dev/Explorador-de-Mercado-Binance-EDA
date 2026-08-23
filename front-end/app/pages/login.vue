<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

// Split próprio (Design.md §5 — painel institucional + form em vidro): sem layout compartilhado.
definePageMeta({ layout: false, middleware: 'guest' })
useHead({ title: 'Entrar · crypto forecasting' })

const route = useRoute()
const { signIn } = useAuthActions()
const redirect = useSupabaseCookieRedirect()

const schema = z.object({
  email: z.email('Informe um e-mail válido.'),
  password: z.string().min(1, 'Informe a senha.'),
})
type Schema = z.output<typeof schema>

const state = reactive<Partial<Schema>>({ email: '', password: '' })
const submitting = ref(false)
const error = ref<string | null>(null)
const hint = ref<string | null>(null)

const expired = computed(() => route.query.reason === 'expired')
const confirmFailed = computed(() => route.query.reason === 'confirm-failed')

const bullets = [
  { title: 'Snapshots diários, não ruído', text: 'Coletamos os top 20 pares USDT da Binance uma vez por dia e calculamos os indicadores por você.' },
  { title: 'Previsões com contexto', text: 'Modelos de ML projetam os cenários de melhor caso, esperado e pior caso sobre o gráfico real.' },
  { title: 'Alertas do que importa', text: 'Volatilidade, volume e o gap entre preço real e projeção, no seu primeiro acesso do dia.' },
] as const

async function onSubmit(event: FormSubmitEvent<Schema>) {
  error.value = null
  hint.value = null
  submitting.value = true
  try {
    const result = await signIn(event.data.email, event.data.password)
    if (!result.ok) {
      error.value = result.message ?? AUTH_COPY.invalidCredentials
      hint.value = result.hint ?? null
      return
    }
    const target = redirect.pluck()
    await navigateTo(target && target.startsWith('/') && !target.startsWith('/login') ? target : '/')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-dvh">
    <!-- Painel institucional (esquerda) -->
    <section
      class="relative hidden flex-[1.1] flex-col border-r border-default px-14 py-9 lg:flex"
      :style="{ background: 'radial-gradient(900px 500px at 30% 20%, rgba(62,134,247,.14), transparent 60%), var(--cf-bg-deep)' }"
    >
      <div class="flex items-center gap-2.5">
        <AppLogo :size="34" />
        <span class="text-[17px] font-semibold text-highlighted">crypto forecasting</span>
      </div>

      <div class="flex max-w-[540px] flex-1 flex-col justify-center gap-6">
        <img
          src="/crypto-forecasting-logo-v5.png"
          alt="Logo: velas de vidro com seta de alta em azul elétrico"
          class="-ml-2 size-[170px] rounded-3xl object-contain"
          style="mix-blend-mode: screen"
          draggable="false"
        >
        <div>
          <h1 class="text-[31px] font-bold leading-[1.2] tracking-[-.02em] text-highlighted">
            Enxergue o mercado um dia à frente.
          </h1>
          <p class="mt-2.5 max-w-[46ch] text-[15px] text-muted">
            Forecasting de criptomoedas com dados reais da Binance, indicadores técnicos e previsões de IA.
          </p>
        </div>
        <ul class="flex flex-col gap-3.5">
          <li
            v-for="b in bullets"
            :key="b.title"
            class="flex items-start gap-3"
          >
            <span class="bg-primary-soft inline-flex size-[30px] flex-none items-center justify-center rounded-lg border border-[rgba(62,134,247,.3)] text-ai">
              <UIcon
                name="i-lucide-check"
                class="size-[15px]"
              />
            </span>
            <span>
              <span class="block font-medium text-highlighted">{{ b.title }}</span>
              <span class="text-[12.5px] text-muted">{{ b.text }}</span>
            </span>
          </li>
        </ul>
      </div>

      <footer class="flex items-center justify-between gap-3">
        <span class="text-[12.5px] text-muted">Projeto desenvolvido por Gabriel Castro</span>
        <span class="inline-flex gap-2">
          <a
            href="https://github.com/gabriel-castro-dev"
            target="_blank"
            rel="noopener"
            aria-label="GitHub de Gabriel Castro"
            class="inline-flex size-[34px] items-center justify-center rounded-lg border border-default transition-colors hover:border-accented"
          >
            <img
              src="/github.png"
              alt=""
              class="size-4 opacity-80"
              style="filter: invert(.92)"
            >
          </a>
          <a
            href="https://www.linkedin.com/in/gabriel-castro-inacio-113523284/"
            target="_blank"
            rel="noopener"
            aria-label="LinkedIn de Gabriel Castro"
            class="inline-flex size-[34px] items-center justify-center rounded-lg border border-default transition-colors hover:border-accented"
          >
            <img
              src="/linkedin.png"
              alt=""
              class="size-4 opacity-80"
              style="filter: invert(.92)"
            >
          </a>
        </span>
      </footer>
    </section>

    <!-- Form (direita) -->
    <section class="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-10">
      <!-- Marca compacta no mobile (o painel esquerdo some) -->
      <div class="flex flex-col items-center gap-2 text-center lg:hidden">
        <AppLogo :size="64" />
        <h1 class="text-[22px] font-bold tracking-[-.01em] text-highlighted">
          Enxergue o mercado um dia à frente.
        </h1>
      </div>

      <UAlert
        v-if="expired"
        class="w-full max-w-[400px]"
        color="neutral"
        variant="subtle"
        icon="i-lucide-clock"
        role="status"
        :description="AUTH_COPY.sessionExpired"
      />
      <UAlert
        v-else-if="confirmFailed"
        class="w-full max-w-[400px]"
        color="neutral"
        variant="subtle"
        icon="i-lucide-mail-warning"
        role="status"
        :description="AUTH_COPY.confirmFailed"
      />

      <div class="glass w-full max-w-[400px] p-[30px] pb-[26px]">
        <h2 class="text-[22px] font-bold tracking-[-.01em] text-highlighted">
          Entrar
        </h2>
        <p class="mt-1 text-[13px] text-muted">
          Use o e-mail e a senha da sua conta.
        </p>

        <UForm
          :schema="schema"
          :state="state"
          class="mt-5 space-y-4"
          @submit="onSubmit"
        >
          <AuthAlert
            :message="error"
            :hint="hint"
          />

          <UFormField
            name="email"
            label="E-mail"
            size="lg"
          >
            <UInput
              v-model="state.email"
              type="email"
              autocomplete="email"
              icon="i-lucide-mail"
              placeholder="voce@exemplo.com"
              size="lg"
              class="w-full"
            />
          </UFormField>

          <UFormField
            name="password"
            label="Senha"
            size="lg"
          >
            <template #hint>
              <NuxtLink
                to="/forgot-password"
                class="text-[12px] text-primary"
              >
                Esqueci a senha
              </NuxtLink>
            </template>
            <AuthPasswordField
              v-model="state.password"
              autocomplete="current-password"
            />
          </UFormField>

          <UButton
            type="submit"
            block
            size="lg"
            class="btn-glow"
            :loading="submitting"
            :label="submitting ? 'Entrando…' : 'Entrar'"
          />
        </UForm>

        <p class="mt-5 text-center text-[13px] text-muted">
          Não tem conta?
          <NuxtLink
            to="/signup"
            class="text-primary"
          >
            Criar conta
          </NuxtLink>
        </p>
      </div>

      <p class="num text-[11px] text-dimmed">
        Dados da Binance · snapshots diários · horários em UTC
      </p>
    </section>
  </div>
</template>
