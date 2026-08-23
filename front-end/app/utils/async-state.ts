/**
 * Variante única de estado assíncrono (Design.md §15): `idle | loading | empty |
 * error | ready`. Substitui combinações booleanas conflitantes espalhadas pelas
 * telas — a regra de "manter o dado anterior esmaecido" fica em `isRefreshing`.
 */

export type AsyncStatus = 'idle' | 'pending' | 'success' | 'error'
export type AsyncView = 'idle' | 'loading' | 'empty' | 'error' | 'ready'

/**
 * `hasData` vence `pending`: ao trocar de ativo o conteúdo anterior continua na
 * tela (esmaecido) até o novo chegar, preservando a geometria.
 */
export function asyncView(status: AsyncStatus, hasData: boolean): AsyncView {
  if (status === 'error' && !hasData) return 'error'
  if (hasData) return 'ready'
  if (status === 'pending') return 'loading'
  if (status === 'idle') return 'idle'
  return 'empty'
}

/** Recarregando por cima de dado já visível (aria-busy + opacidade). */
export function isRefreshing(status: AsyncStatus, hasData: boolean): boolean {
  return status === 'pending' && hasData
}
