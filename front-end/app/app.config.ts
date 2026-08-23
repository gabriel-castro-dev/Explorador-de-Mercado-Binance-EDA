/**
 * Tema Nuxt UI para o design v3 "Observatório Vivo" (docs/design/Design.md).
 *
 * Regras que este arquivo faz valer:
 * - primária "electric" #3E86F7 (ação, foco, navegação ativa e link);
 * - ciano/gelo/vermelho de dados vivem em `utils/constants.ts` + tokens `--cf-*`,
 *   nunca em `success`/`error` do tema;
 * - `--cf-best` (verde) é exclusivo do melhor cenário no Monte Carlo;
 * - superfície delimitada só em input, popover, menu, modal, drawer, estado e dock
 *   (Design.md §5.1) — por isso o UCard perde qualquer receita de "vidro".
 */
export default defineAppConfig({
  ui: {
    colors: {
      primary: 'electric',
      neutral: 'zinc', // os neutros reais vêm dos --ui-* em main.css (navy/gelo)
    },
    icons: {
      loading: 'i-lucide-loader-circle',
    },
    button: {
      // Microinteração: 180–280 ms, sem animar propriedades de layout.
      slots: { base: 'transition-[color,background-color,border-color,opacity] duration-200 ease-[cubic-bezier(0.2,0.8,0.2,1)]' },
    },
    modal: {
      slots: { content: 'rounded-xl ring-[var(--cf-hairline)]' },
    },
    drawer: {
      slots: { content: 'ring-[var(--cf-hairline)]' },
    },
    popover: {
      slots: { content: 'rounded-xl ring-[var(--cf-hairline)]' },
    },
    dropdownMenu: {
      slots: { content: 'rounded-xl ring-[var(--cf-hairline)]' },
    },
    selectMenu: {
      slots: { content: 'rounded-xl ring-[var(--cf-hairline)]' },
    },
    tooltip: {
      slots: { content: 'rounded-lg ring-[var(--cf-hairline)]' },
    },
  },
})
