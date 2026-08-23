// Tema Dark-Tech (Design.md v2): navy quase-preto + vidro; primária "electric" #3e86f7
// (iluminação seletiva, ≤ 20 % da composição); ciano #5fc4ff EXCLUSIVO de conteúdo de IA;
// alta/baixa só via tokens --cf-up/--cf-down (gelo × vermelho), nunca success/error do Nuxt UI.
// Camadas flutuantes (modal/drawer/menu) ficam sólidas via tokens --ui-bg* — não sobrescrever
// os slots delas aqui (as strings substituem classes de posicionamento do tema).
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
      // Todo UCard é um cartão de vidro (receita única em main.css); a variante
      // outline é neutralizada para o bg-default/ring não competir com o vidro.
      slots: {
        root: 'glass overflow-hidden',
      },
      variants: {
        variant: {
          outline: {
            root: 'divide-y divide-[var(--cf-border-muted)]',
          },
        },
      },
    },
  },
})
