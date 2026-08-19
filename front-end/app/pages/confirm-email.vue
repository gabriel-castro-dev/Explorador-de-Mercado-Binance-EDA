<script setup lang="ts">
definePageMeta({ layout: 'auth', middleware: 'guest' })
useHead({ title: 'Verifique seu e-mail · crypto forecasting' })

const pendingEmail = usePendingEmail()
const { resendConfirmation } = useAuthActions()
const toast = useToast()

// Sem e-mail pendente (acesso direto) → volta ao cadastro.
if (!pendingEmail.value) await navigateTo('/signup')

const COOLDOWN = 60
const cooldown = ref(COOLDOWN)
const sending = ref(false)
let timer: ReturnType<typeof setInterval> | undefined

function startCooldown() {
  cooldown.value = COOLDOWN
  clearInterval(timer)
  timer = setInterval(() => {
    cooldown.value -= 1
    if (cooldown.value <= 0) clearInterval(timer)
  }, 1000)
}
onMounted(startCooldown)
onBeforeUnmount(() => clearInterval(timer))

const cooldownLabel = computed(() => `0:${String(Math.max(0, cooldown.value)).padStart(2, '0')}`)

async function resend() {
  sending.value = true
  try {
    const r = await resendConfirmation(pendingEmail.value)
    toast.add({ title: r.message ?? AUTH_COPY.resendSent, color: 'neutral', icon: 'i-lucide-mail' })
    startCooldown()
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="text-center">
    <div class="mx-auto flex size-11 items-center justify-center rounded-full bg-primary-soft text-primary">
      <UIcon
        name="i-lucide-inbox"
        class="size-6"
      />
    </div>
    <h1 class="mt-4 text-[20px] font-semibold text-highlighted">
      Verifique seu e-mail
    </h1>
    <p
      class="mt-2 text-[13px] text-muted"
      role="status"
    >
      Se este e-mail for novo, enviamos um link de confirmação para
      <span class="num text-default">{{ pendingEmail }}</span>. O link vale por 24 horas.
    </p>

    <div class="mt-5 rounded-md border border-default bg-muted px-4 py-3 text-left text-[13px]">
      <p class="text-muted">
        Não chegou? Confira o spam.
        <span v-if="cooldown > 0">Você pode pedir outro link em <span class="num text-default">{{ cooldownLabel }}</span>.</span>
      </p>
      <UButton
        class="mt-3"
        color="neutral"
        variant="outline"
        size="sm"
        :disabled="cooldown > 0"
        :loading="sending"
        label="Reenviar link"
        icon="i-lucide-refresh-cw"
        @click="resend"
      />
    </div>

    <p class="mt-5 text-[13px]">
      <NuxtLink
        to="/login"
        class="text-primary"
      >
        Voltar para entrar
      </NuxtLink>
    </p>
  </div>
</template>
