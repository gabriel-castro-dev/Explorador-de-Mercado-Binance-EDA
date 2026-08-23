import type { DailyReading } from '~/types/api'

/**
 * Leitura do dia (texto gerado por LLM no back-end, cache global por dia UTC).
 * Erro/503 nunca bloqueia o resto do Início — o card mostra estado vazio + retry.
 */
export function useDailyReading() {
  const api = useApi()
  return useAsyncData<DailyReading | null>(
    'daily-reading',
    () => api.get('/api/v1/insights/daily-reading'),
    { default: () => null },
  )
}
