<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

// Sem middleware guest: a sessão de recuperação é uma sessão válida.
definePageMeta({ layout: 'auth' })
useHead({ title: 'Redefinir senha · crypto forecasting' })

const session = useSupabaseSession()
const user = useSupabaseUser()
const authHash = useState<{ type: string | null, error: string | null }>('cf-auth-hash')
const supabase = useSupabaseClient()
const { updatePassword } = useAuthActions()
const toast = useToast()

// Pronto quando há sessão (o link de recuperação já foi consumido pelo supabase-js) ou evento PASSWORD_RECOVERY.
const ready = ref(!!session.value)
const linkInvalid = ref(!!authHash.value?.error)
watch(session, (s) => {
  if (s) ready.value = true
}, { immediate: true })
onMounted(() => {
  const { data } = supabase.auth.onAuthStateChange((event) => {
    if (event === 'PASSWORD_RECOVERY') ready.value = true
  })
  onBeforeUnmount(() => data.subscription.unsubscribe())
  // Sem sessão após um instante → link expirado/inválido.
  setTimeout(() => {
    if (!ready.value) linkInvalid.value = true
  }, 4000)
})

const email = computed(() => (user.value?.email as string | undefined) ?? '')

const schema = z.object({
  password: z.string().min(8, 'A senha precisa ter pelo menos 8 caracteres.'),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, { message: 'As senhas não coincidem.', path: ['confirm'] })
type Schema = z.output<typeof schema>
const state = reactive<Partial<Schema>>({ password: '', confirm: '' })
const submitting = ref(false)
const error = ref<string | null>(null)

async function onSubmit(event: FormSubmitEvent<Schema>) {
  error.value = null
  submitting.value = true
  try {
    const r = await updatePassword(event.data.password)
    if (!r.ok) {
      error.value = r.message ?? AUTH_COPY.passwordUpdateFailed
      return
    }
    toast.add({ title: AUTH_COPY.passwordUpdated, color: 'neutral', icon: 'i-lucide-check' })
    await navigateTo('/', { replace: true })
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-[20px] font-semibold text-highlighted">
      Redefinir senha
    </h1>
    <p class="mt-1 text-[13px] text-muted">
      Crie uma nova senha<template v-if="email">
        para <span class="num text-default">{{ email }}</span>
      </template>.
    </p>

    <div
      v-if="!ready && linkInvalid"
      class="mt-5 rounded-md border border-default bg-muted px-4 py-3 text-[13px]"
      role="status"
    >
      Link expirado ou inválido?
      <NuxtLink
        to="/forgot-password"
        class="text-primary"
      >
        Peça um novo
      </NuxtLink>.
    </div>
    <div
      v-else-if="!ready"
      class="mt-5 flex items-center gap-2 text-[13px] text-muted"
      role="status"
      aria-busy="true"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="size-4 animate-spin"
      /> Validando o link…
    </div>

    <UForm
      v-else
      :schema="schema"
      :state="state"
      class="mt-5 space-y-4"
      @submit="onSubmit"
    >
      <AuthAlert :message="error" />

      <UFormField
        name="password"
        label="Nova senha"
        size="lg"
      >
        <AuthPasswordField
          v-model="state.password"
          autocomplete="new-password"
          show-strength
        />
      </UFormField>
      <UFormField
        name="confirm"
        label="Confirmar nova senha"
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
        :label="submitting ? 'Salvando…' : 'Salvar nova senha'"
      />
    </UForm>
  </div>
</template>
