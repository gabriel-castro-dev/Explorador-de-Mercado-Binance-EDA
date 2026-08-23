import { usePreferredReducedMotion } from '@vueuse/core'
import type { MaybeComputedElementRef } from '@vueuse/core'

/**
 * Redução de movimento global (Design.md §7.3): vídeo do Login vira poster,
 * gráficos e trajetórias aparecem completos, pinning/parallax/stagger somem.
 * Reativo — a preferência pode mudar com a aba aberta.
 */
export function useReducedMotion(): ComputedRef<boolean> {
  const pref = usePreferredReducedMotion()
  return computed(() => pref.value === 'reduce')
}

/**
 * Atraso de entrada em lista, em ms (stagger 40–70 ms por linha, Design.md §7.2).
 * Devolve `0` sob redução de movimento — a lista aparece de uma vez.
 */
export function useStagger(step = 55, max = 10) {
  const reduced = useReducedMotion()
  return (index: number) => (reduced.value ? 0 : Math.min(index, max) * step)
}

/**
 * "Entrou no viewport" — uma única vez, para desenhos progressivos (trajetória
 * SVG, arcos de horizonte, Monte Carlo). Sob redução de movimento nasce `true`:
 * o desenho aparece completo, sem animação progressiva.
 */
export function useEnterOnce(
  target: MaybeComputedElementRef,
  threshold = 0.2,
): Ref<boolean> {
  const entered = ref(false)
  const reduced = useReducedMotion()

  onMounted(() => {
    if (reduced.value) entered.value = true
  })

  const { stop } = useIntersectionObserver(target, (entries) => {
    if (!entries[0]?.isIntersecting) return
    entered.value = true
    stop()
  }, { threshold })

  return entered
}
