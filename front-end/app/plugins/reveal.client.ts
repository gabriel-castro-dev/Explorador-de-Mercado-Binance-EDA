import { prefersReducedMotion } from '~/utils/motion'

interface RevealOptions {
  /** Atraso em ms (stagger de lista: 40–70 ms por linha). */
  delay?: number
  /** Deslocamento inicial em px (24–40 conforme Design.md §7.1). */
  y?: number
}

const observed = new WeakMap<Element, IntersectionObserver>()

function reveal(el: HTMLElement) {
  el.classList.add('cf-reveal-in')
}

/**
 * `v-reveal` — entrada de seção (700–900 ms, cubic-bezier(0.32,0.72,0,1)),
 * uma única vez, quando a seção entra no viewport (Design.md §7.1).
 *
 * Sob `prefers-reduced-motion: reduce` o elemento nasce visível: nenhum
 * conteúdo depende da animação.
 */
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.directive<HTMLElement, RevealOptions | number | undefined>('reveal', {
    mounted(el, binding) {
      const opts: RevealOptions = typeof binding.value === 'number' ? { delay: binding.value } : (binding.value ?? {})
      if (opts.delay) el.style.setProperty('--cf-reveal-delay', `${opts.delay}ms`)
      if (opts.y !== undefined) el.style.setProperty('--cf-reveal-y', `${opts.y}px`)

      if (prefersReducedMotion() || typeof IntersectionObserver === 'undefined') return

      el.classList.add('cf-reveal')
      const observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          reveal(el)
          observer.disconnect()
          observed.delete(el)
        }
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' })
      observer.observe(el)
      observed.set(el, observer)
    },
    unmounted(el) {
      observed.get(el)?.disconnect()
      observed.delete(el)
    },
  })
})
