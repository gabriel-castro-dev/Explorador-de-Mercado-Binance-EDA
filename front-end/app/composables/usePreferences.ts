import type { PreferencesIn, PreferencesOut } from '~/types/api'
import { formatBrPhoneDisplay, parsePhoneInput } from '~/utils/phone'
import { messageOf } from '~/utils/api-errors'

export interface PreferencesForm {
  displayName: string
  /** Como digitado/exibido (máscara BR); convertido para E.164 só no PUT. */
  phone: string
  notificationsEnabled: boolean
  topics: { forecast_gap: boolean, volume_movers: boolean, volatility: boolean, model_runs: boolean }
  /** UI "Velas de alta preenchidas" = inverso de chart.hollow_up_candles. */
  filledCandles: boolean
}

function toForm(data: PreferencesOut | null): PreferencesForm {
  return {
    displayName: data?.display_name ?? '',
    phone: formatBrPhoneDisplay(data?.phone),
    notificationsEnabled: data?.notifications?.enabled ?? false,
    topics: {
      forecast_gap: data?.notifications?.topics?.forecast_gap ?? false,
      volume_movers: data?.notifications?.topics?.volume_movers ?? false,
      volatility: data?.notifications?.topics?.volatility ?? false,
      model_runs: data?.notifications?.topics?.model_runs ?? false,
    },
    // Vazada é o padrão do design; na primeira carga (sem doc salvo) seguimos o padrão local.
    filledCandles: data?.chart ? !data.chart.hollow_up_candles : false,
  }
}

/**
 * Preferências do usuário (GET/PUT /api/v1/preferences, Firestore atrás da API).
 * Salvamento explícito (botão), não otimista. O corpo do PUT é montado campo a
 * campo — nunca espalhar o GET (a API rejeita `email`/`user_id` com 422).
 */
export function usePreferences() {
  const api = useApi()
  const toast = useToast()
  const hollow = useHollowCandles()

  const { data, status, error, refresh } = useAsyncData<PreferencesOut | null>(
    'preferences',
    () => api.get('/api/v1/preferences'),
    { default: () => null },
  )

  const form = reactive<PreferencesForm>(toForm(null))
  const fieldErrors = reactive<{ displayName: string | null, phone: string | null }>({ displayName: null, phone: null })
  const saving = ref(false)

  let snapshot = JSON.stringify(form)
  function hydrate(from: PreferencesOut | null) {
    Object.assign(form, toForm(from))
    snapshot = JSON.stringify(form)
    // Servidor vence o estado local do navegador (write-through na volta).
    if (from?.chart) hollow.value = from.chart.hollow_up_candles
  }
  watch(data, hydrate, { immediate: true })

  const dirty = computed(() => JSON.stringify(form) !== snapshot)
  const email = computed(() => data.value?.email ?? null)

  function validate(): PreferencesIn | null {
    fieldErrors.displayName = null
    fieldErrors.phone = null
    const displayName = form.displayName.trim()
    if (displayName.length > 120) {
      fieldErrors.displayName = 'Use no máximo 120 caracteres.'
      return null
    }
    let phone: string | null = null
    if (form.phone.trim()) {
      phone = parsePhoneInput(form.phone)
      if (!phone) {
        fieldErrors.phone = 'Informe DDD + número (ex.: (11) 91234-5678) ou o formato internacional +55…'
        return null
      }
    }
    return {
      display_name: displayName || null,
      phone,
      notifications: {
        enabled: form.notificationsEnabled,
        channel: 'email', // único canal ativo; SMS/WhatsApp são "Em breve"
        topics: { ...form.topics },
      },
      chart: { hollow_up_candles: !form.filledCandles },
    }
  }

  async function save(): Promise<boolean> {
    if (saving.value) return false
    const body = validate()
    if (!body) return false
    saving.value = true
    try {
      const saved = await api.put('/api/v1/preferences', { body })
      data.value = saved
      hydrate(saved)
      toast.add({ title: 'Preferências salvas.', color: 'neutral', icon: 'i-lucide-check' })
      return true
    } catch (e) {
      toast.add({ title: 'Não foi possível salvar as preferências.', description: messageOf(e), color: 'neutral', icon: 'i-lucide-circle-alert' })
      return false
    } finally {
      saving.value = false
    }
  }

  return { data, status, error, refresh, form, fieldErrors, dirty, saving, email, save }
}
