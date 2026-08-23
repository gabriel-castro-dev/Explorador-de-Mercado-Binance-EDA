<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Esqueci a senha · CRYPTO FORECASTING' })

const { forgotPassword } = useAuthActions()

const schema = z.object({ email: z.email('Informe um e-mail válido.') })
type Schema = z.output<typeof schema>
const state = reactive<Partial<Schema>>({ email: '' })

const submitting = ref(false)
const sent = ref(false)
const error = ref<string | null>(null)
const COOLDOWN = 60
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | undefined

function startCooldown() {
  cooldown.value = COOLDOWN
  clearInterval(timer)
  timer = setInterval(() => {
    cooldown.value -= 1
    if (cooldown.value <= 0) clearInterval(timer)
  }, 1000)
}
onBeforeUnmount(() => clearInterval(timer))

async function onSubmit(event: FormSubmitEvent<Schema>) {
  error.value = null
  submitting.value = true
  try {
    const r = await forgotPassword(event.data.email)
    if (!r.ok) {
      error.value = r.message ?? AUTH_COPY.forgotNetwork
      return
    }
    sent.value = true
    startCooldown()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <NuxtLink
      to="/login"
      class="inline-flex items-center gap-1 text-[12px] text-muted hover:text-default"
    >
      <UIcon
        name="i-lucide-arrow-left"
        class="size-3.5"
      /> Voltar
    </NuxtLink>
    <h1 class="cf-h1 mt-4">
      Esqueci a senha
    </h1>
    <p class="mt-2 text-[15px] text-muted">
      Informe o e-mail da conta. Enviaremos um link para criar uma nova senha.
    </p>

    <UForm
      :schema="schema"
      :state="state"
      class="mt-7 space-y-5"
      @submit="onSubmit"
    >
      <AuthAlert :message="error" />
      <AuthAlert
        v-if="sent"
        tone="status"
        :message="AUTH_COPY.forgotSent"
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

      <UButton
        type="submit"
        block
        size="lg"
        :loading="submitting"
        :disabled="cooldown > 0"
        :label="sent ? (cooldown > 0 ? `Enviar de novo (${cooldown}s)` : 'Enviar de novo') : 'Enviar link'"
      />
    </UForm>
  </div>
</template>
