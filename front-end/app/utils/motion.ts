/**
 * Preferência de movimento (Design.md §7.3) fora do ciclo reativo — para
 * canvas, IntersectionObserver e diretivas, onde não há `setup()`.
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Conexão econômica (`saveData`) — usada para não baixar o vídeo do Login. */
export function prefersSavedData(): boolean {
  if (typeof navigator === 'undefined') return false
  const connection = (navigator as { connection?: { saveData?: boolean } }).connection
  return connection?.saveData === true
}

/** Curvas normativas (Design.md §7.1). */
export const EASE_SECTION = 'cubic-bezier(0.32, 0.72, 0, 1)'
export const EASE_MICRO = 'cubic-bezier(0.2, 0.8, 0.2, 1)'

/** `cubic-bezier(0.32,0.72,0,1)` avaliada em JS (desenho progressivo em canvas/SVG). */
export function easeSection(t: number): number {
  const x = Math.min(1, Math.max(0, t))
  // Aproximação estável da curva CSS: forte no início, assíntota suave no fim.
  return 1 - (1 - x) ** 3
}
