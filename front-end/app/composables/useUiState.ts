import { useLocalStorage } from '@vueuse/core'
import { STORAGE_KEYS } from '~/utils/constants'

/** Estado de UI compartilhado entre layout e páginas (drawer de indicadores no mobile). */
export const useIndicatorsDrawer = () => useState<boolean>('cf-indicators-drawer', () => false)

/** Preferência de acessibilidade: velas de alta vazadas (ux-spec §9). */
export const useHollowCandles = () => useLocalStorage<boolean>(STORAGE_KEYS.hollowCandles, false)

/** Dica de primeiro acesso já dispensada? */
export const useOnboarded = () => useLocalStorage<boolean>(STORAGE_KEYS.onboarded, false)

/** E-mail do cadastro recém-enviado (para a tela "Verifique seu e-mail"); só em memória. */
export const usePendingEmail = () => useState<string>('cf-pending-email', () => '')
