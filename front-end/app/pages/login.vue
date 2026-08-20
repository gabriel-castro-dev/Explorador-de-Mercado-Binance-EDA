<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'auth', middleware: 'guest' })
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
  <div>
    <UAlert
      v-if="expired"
      class="mb-4"
      color="neutral"
      variant="subtle"
      icon="i-lucide-clock"
      role="status"
      :description="AUTH_COPY.sessionExpired"
    />
    <UAlert
      v-else-if="confirmFailed"
      class="mb-4"
      color="neutral"
      variant="subtle"
      icon="i-lucide-mail-warning"
      role="status"
      :description="AUTH_COPY.confirmFailed"
    />

    <h1 class="text-[20px] font-semibold text-highlighted">
      Entrar
    </h1>
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
</template>
