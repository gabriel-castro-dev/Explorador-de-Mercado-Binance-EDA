<script setup lang="ts">
/** Callback dos links de e-mail (ux-spec §3.4): só spinner; decide o destino pela sessão + tipo do link. */
definePageMeta({ layout: 'auth' })
useHead({ title: 'Confirmando… · crypto forecasting' })

const session = useSupabaseSession()
const authHash = useState<{ type: string | null, error: string | null }>('cf-auth-hash')
const toast = useToast()

const TIMEOUT_MS = 8000
let timer: ReturnType<typeof setTimeout> | undefined
let done = false

async function finish(target: string, toastTitle?: string) {
  if (done) return
  done = true
  clearTimeout(timer)
  if (toastTitle) toast.add({ title: toastTitle, color: 'neutral', icon: 'i-lucide-check' })
  await navigateTo(target, { replace: true })
}

onMounted(() => {
  if (authHash.value?.error) {
    void finish('/login?reason=confirm-failed')
    return
  }
  timer = setTimeout(() => void finish('/login?reason=confirm-failed'), TIMEOUT_MS)
  watch(session, (s) => {
    if (!s) return
    if (authHash.value?.type === 'recovery') void finish('/reset-password')
    else void finish('/', AUTH_COPY.emailConfirmed)
  }, { immediate: true })
})

onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <div
    class="flex flex-col items-center py-4 text-center"
    aria-busy="true"
    role="status"
  >
    <UIcon
      name="i-lucide-loader-circle"
      class="size-6 animate-spin text-primary"
    />
    <p class="mt-3 text-[13px] text-muted">
      Confirmando…
    </p>
  </div>
</template>
