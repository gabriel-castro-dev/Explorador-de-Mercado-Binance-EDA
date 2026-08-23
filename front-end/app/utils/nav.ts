/** Navegação principal — a mesma ordem no header desktop e na barra inferior mobile (Design.md §6). */
export interface NavItem {
  label: string
  to: string
  icon: string
  /** `/` casa exato; as demais casam por prefixo. */
  exact?: boolean
}

export const MAIN_NAV: readonly NavItem[] = [
  { label: 'INÍCIO', to: '/', icon: 'i-lucide-house', exact: true },
  { label: 'GRÁFICOS', to: '/graficos', icon: 'i-lucide-chart-candlestick' },
  { label: 'PREVISÕES', to: '/previsoes', icon: 'i-lucide-git-fork' },
  { label: 'MERCADO', to: '/mercado', icon: 'i-lucide-table-2' },
] as const

export function isNavActive(item: NavItem, path: string): boolean {
  return item.exact ? path === item.to : path.startsWith(item.to)
}
