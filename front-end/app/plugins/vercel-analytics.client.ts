import { inject } from '@vercel/analytics'

/**
 * Vercel Web Analytics (page views + visitantes, sem cookies).
 * Só no navegador e só em produção: em dev/preview o script não é injetado,
 * evitando ruído nas métricas e chamadas de rede nos testes.
 * O `<script>` de coleta só existe quando servido pela Vercel; fora dela falha em silêncio.
 */
export default defineNuxtPlugin({
  name: 'cf-vercel-analytics',
  setup() {
    if (import.meta.dev) return
    inject({ mode: 'production' })
  },
})
