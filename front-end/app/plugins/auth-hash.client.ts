/**
 * Captura o fragmento de auth (`#access_token=…&type=signup|recovery`) ANTES do supabase-js
 * consumi-lo e limpar o hash (acontece na inicialização do client, no plugin do módulo, order -20).
 * As páginas /confirm e /reset-password usam isso para saber o tipo do link.
 */
export default defineNuxtPlugin({
  name: 'cf-auth-hash',
  order: -30,
  setup() {
    const captured = useState<{ type: string | null, error: string | null, errorDescription: string | null }>('cf-auth-hash', () => ({ type: null, error: null, errorDescription: null }))
    const hash = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : ''
    if (!hash) return
    const params = new URLSearchParams(hash)
    if (params.has('access_token') || params.has('error') || params.has('type')) {
      captured.value = {
        type: params.get('type'),
        error: params.get('error') ?? params.get('error_code'),
        errorDescription: params.get('error_description'),
      }
    }
  },
})
