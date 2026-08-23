import type { Timeframe } from '~/types/api'
import { DEFAULT_TIMEFRAME, isTimeframe } from '~/utils/constants'

/**
 * Estado do dashboard na URL (`/graficos?symbol=BTCUSDT&tf=1h`): links compartilháveis e restauráveis
 * após login expirado. `tf` inválido é corrigido silenciosamente para o padrão (ux-spec §7).
 */
export function useDashboardQuery() {
  const route = useRoute()
  const router = useRouter()

  function write(patch: { symbol?: string | null, tf?: Timeframe }) {
    const query: Record<string, string> = {}
    for (const [k, v] of Object.entries(route.query)) if (typeof v === 'string') query[k] = v
    if (patch.symbol !== undefined) {
      if (patch.symbol) query.symbol = patch.symbol
      else delete query.symbol
    }
    if (patch.tf !== undefined) query.tf = patch.tf
    return router.replace({ query })
  }

  const symbol = computed<string | null>({
    get: () => {
      const raw = route.query.symbol
      return typeof raw === 'string' && raw.trim() ? raw.trim().toUpperCase() : null
    },
    set: value => void write({ symbol: value }),
  })

  const tf = computed<Timeframe>({
    get: () => {
      const raw = route.query.tf
      return isTimeframe(raw) ? raw : DEFAULT_TIMEFRAME
    },
    set: value => void write({ tf: value }),
  })

  /** Escreve o símbolo inicial na URL sem empilhar histórico. */
  function ensureSymbol(fallback: string | null) {
    if (!symbol.value && fallback) return write({ symbol: fallback, tf: tf.value })
    if (symbol.value && route.query.tf !== tf.value) return write({ tf: tf.value })
    return Promise.resolve()
  }

  return { symbol, tf, ensureSymbol }
}
