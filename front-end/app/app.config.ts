// Tema Dark-Tech (Design.md v2): navy quase-preto + vidro; primária "electric" #3e86f7
// (iluminação seletiva, ≤ 20 % da composição); ciano #5fc4ff EXCLUSIVO de conteúdo de IA;
// alta/baixa só via tokens --cf-up/--cf-down (gelo × vermelho), nunca success/error do Nuxt UI.
export default defineAppConfig({
  ui: {
    colors: {
      primary: 'electric',
      neutral: 'zinc', // neutros reais vêm dos --ui-* em main.css (navy/gelo)
    },
    icons: {
      loading: 'i-lucide-loader-circle',
    },
    card: {
      // Todo UCard é um cartão de vidro (receita única em main.css).
      slots: {
        root: 'glass divide-y divide-[var(--cf-border-muted)] ring-0 rounded-[12px]',
      },
    },
    modal: {
      // Camadas flutuantes são sólidas (vidro atrás de vidro embaralha a leitura).
      slots: {
        content: 'bg-solid-surface ring ring-[var(--cf-border)] rounded-[12px]',
      },
    },
    drawer: {
      slots: {
        content: 'bg-solid-surface ring ring-[var(--cf-border)]',
      },
    },
    dropdownMenu: {
      slots: {
        content: 'bg-solid-surface ring ring-[var(--cf-border)]',
      },
    },
    tooltip: {
      slots: {
        content: 'bg-solid-surface ring ring-[var(--cf-border)]',
      },
    },
  },
})
