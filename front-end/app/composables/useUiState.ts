import { useLocalStorage } from '@vueuse/core'
import { STORAGE_KEYS } from '~/utils/constants'

/** Estado de UI compartilhado entre layout e páginas (drawer de indicadores no mobile). */
export const useIndicatorsDrawer = () => useState<boolean>('cf-indicators-drawer', () => false)

/**
 * Vela de alta vazada (padrão do Design.md v2 — a cara da logo). A opção de
 * acessibilidade em Preferências é a inversa: "Velas de alta preenchidas".
 */
export const useHollowCandles = () => useLocalStorage<boolean>(STORAGE_KEYS.hollowCandles, true)

/** Cenários do modelo (melhor/esperado/pior) visíveis no gráfico. */
export const useScenarioPref = () => useLocalStorage<boolean>(STORAGE_KEYS.scenarios, true)

/** Dica de primeiro acesso já dispensada? */
export const useOnboarded = () => useLocalStorage<boolean>(STORAGE_KEYS.onboarded, false)

/** Último símbolo aberto em /graficos (atalho "Continuar de onde parou" no Início). */
export const useLastSymbol = () => useLocalStorage<string>(STORAGE_KEYS.lastSymbol, '')

/** E-mail do cadastro recém-enviado (para a tela "Verifique seu e-mail"); só em memória. */
export const usePendingEmail = () => useState<string>('cf-pending-email', () => '')

/**
 * "Desde o seu último acesso": guarda o acesso anterior por navegador
 * (a API de preferências não tem last_seen_at neste marco — ver plano/marco 3).
 * Captura o valor anterior uma vez por sessão antes de sobrescrever.
 */
export function useLastSeen(): Readonly<Ref<string | null>> {
  const previous = useState<string | null>('cf-last-seen-previous', () => null)
  const stored = useLocalStorage<string>(STORAGE_KEYS.lastSeenAt, '')
  const captured = useState<boolean>('cf-last-seen-captured', () => false)
  if (!captured.value) {
    captured.value = true
    previous.value = stored.value || null
    stored.value = new Date().toISOString()
  }
  return readonly(previous)
}
