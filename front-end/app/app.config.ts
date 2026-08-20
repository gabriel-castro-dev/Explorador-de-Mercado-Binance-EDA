// Tema (docs/design/tokens.md): neutros zinc, acento índigo; verde/vermelho só em dados
// (tokens --cf-up/--cf-down em main.css), nunca via success/error do Nuxt UI.
export default defineAppConfig({
  ui: {
    colors: {
      primary: 'indigo',
      neutral: 'zinc',
    },
    icons: {
      loading: 'i-lucide-loader-circle',
    },
  },
})
