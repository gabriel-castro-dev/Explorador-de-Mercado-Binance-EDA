import { useNow } from '@vueuse/core'
import type { MaybeRefOrGetter } from 'vue'
import { STALE_AFTER_HOURS } from '~/utils/constants'
import { formatAgo, formatUtc, hoursSince } from '~/utils/format'

export type FreshnessSource = keyof typeof STALE_AFTER_HOURS
export type FreshnessState = 'loading' | 'error' | 'fresh' | 'stale' | 'empty'

/**
 * Regras do selo de snapshot (ux-spec §6): "há X" calculado a partir do dado carregado,
 * limiar 26 h (velas) / 2 h (resumo 24h). Reavalia a cada minuto.
 */
export function useFreshness(
  source: FreshnessSource,
  lastAt: MaybeRefOrGetter<string | null | undefined>,
  status: MaybeRefOrGetter<'idle' | 'pending' | 'success' | 'error'>,
  /** Limiar em horas (default por fonte); ex.: velas 1d têm open_time de até ~48 h → 50. */
  thresholdHours?: MaybeRefOrGetter<number | undefined>,
) {
  const now = useNow({ interval: 60_000 })
  const limit = computed(() => toValue(thresholdHours) ?? STALE_AFTER_HOURS[source])

  const state = computed<FreshnessState>(() => {
    const s = toValue(status)
    const at = toValue(lastAt)
    if (s === 'error') return 'error'
    if (s === 'pending' && !at) return 'loading'
    if (!at) return 'empty'
    return hoursSince(at, now.value) > limit.value ? 'stale' : 'fresh'
  })

  const isStale = computed(() => state.value === 'stale')
  const ago = computed(() => {
    const at = toValue(lastAt)
    return at ? formatAgo(at, now.value) : '—'
  })
  const atUtc = computed(() => {
    const at = toValue(lastAt)
    return at ? formatUtc(at) : '—'
  })

  const label = computed(() => {
    const at = toValue(lastAt)
    if (state.value === 'loading') return ''
    if (!at) return '—'
    if (source === 'klines') {
      return isStale.value ? `Velas atualizadas em ${atUtc.value} · ${ago.value}` : `Velas: ${atUtc.value} · ${ago.value}`
    }
    return `Resumo 24h: ${atUtc.value} · ${ago.value} · atualiza de hora em hora`
  })

  /** Horas desde o horário esperado da coleta diária (00:05 UTC), para a mensagem do alerta stale. */
  const hoursLate = computed(() => {
    if (source !== 'klines') return 0
    const n = now.value
    const expected = new Date(Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate(), 0, 5))
    if (expected > n) expected.setUTCDate(expected.getUTCDate() - 1)
    return Math.max(0, Math.round((n.getTime() - expected.getTime()) / 3_600_000))
  })

  return { state, isStale, ago, atUtc, label, hoursLate }
}
