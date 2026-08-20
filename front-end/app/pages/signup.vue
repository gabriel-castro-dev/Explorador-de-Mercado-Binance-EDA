<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Criar conta · crypto forecasting' })

const { signUp } = useAuthActions()
const pendingEmail = usePendingEmail()

const schema = z.object({
  email: z.email('Informe um e-mail válido.'),
  password: z.string().min(8, 'A senha precisa ter pelo menos 8 caracteres.'),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, { message: 'As senhas não coincidem.', path: ['confirm'] })
type Schema = z.output<typeof schema>

const state = reactive<Partial<Schema>>({ email: '', password: '', confirm: '' })
const submitting = ref(false)
const error = ref<string | null>(null)
const hint = ref<string | null>(null)

async function onSubmit(event: FormSubmitEvent<Schema>) {
  error.value = null
  hint.value = null
  submitting.value = true
  try {
    const result = await signUp(event.data.email, event.data.password)
    if (!result.ok) {
      error.value = result.message ?? AUTH_COPY.signupNetwork
      hint.value = result.hint ?? null
      return
    }
    // Sempre vai para "verifique seu e-mail", exista ou não a conta (ux-spec §3.2).
    pendingEmail.value = event.data.email
    await navigateTo('/confirm-email')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-[20px] font-semibold text-highlighted">
      Criar conta
    </h1>
    <p class="mt-1 text-[13px] text-muted">
      Você receberá um link para confirmar o e-mail.
    </p>

    <UForm
      :schema="schema"
      :state="state"
      class="mt-5 space-y-4"
      :validate-on-input-delay="300"
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
        help="Mínimo de 8 caracteres."
      >
        <AuthPasswordField
          v-model="state.password"
          autocomplete="new-password"
          show-strength
        />
      </UFormField>

      <UFormField
        name="confirm"
        label="Confirmar senha"
        size="lg"
      >
        <AuthPasswordField
          v-model="state.confirm"
          autocomplete="new-password"
        />
      </UFormField>

      <UButton
        type="submit"
        block
        size="lg"
        :loading="submitting"
        :label="submitting ? 'Criando conta…' : 'Criar conta'"
      />
    </UForm>

    <p class="mt-5 text-center text-[13px] text-muted">
      Já tem conta?
      <NuxtLink
        to="/login"
        class="text-primary"
      >
        Entrar
      </NuxtLink>
    </p>
  </div>
</template>
