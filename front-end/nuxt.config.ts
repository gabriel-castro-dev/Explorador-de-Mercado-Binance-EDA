// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@nuxtjs/supabase',
    '@vueuse/nuxt',
    '@nuxt/test-utils/module',
  ],

  // SPA estático: dashboard atrás de login, API token-only (Bearer) → nada a pré-renderizar.
  // Ver docs/adr/0001-frontend-spa-static.md.
  ssr: false,

  devtools: {
    enabled: true,
  },

  app: {
    head: {
      title: 'CRYPTO FORECASTING',
      htmlAttrs: { lang: 'pt-BR' },
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        { name: 'description', content: 'Forecasting, analytics e inteligencia de mercado sobre snapshots diarios da Binance. Horarios em UTC.' },
        { name: 'color-scheme', content: 'dark' },
        { name: 'theme-color', content: '#050811' },
      ],
      link: [{ rel: 'icon', href: '/favicon.ico' }],
    },
    // Mudanca de rota: opacity/translate discretos (Design.md §7.1) — nunca width/height/top/left.
    pageTransition: { name: 'cf-page', mode: 'out-in' },
  },

  css: ['~/assets/css/main.css'],

  // Dark-only (Design.md §6.1): sem alternancia de tema, sem @nuxtjs/color-mode.
  ui: {
    colorMode: false,
  },

  runtimeConfig: {
    public: {
      // Sobrescrito por NUXT_PUBLIC_API_BASE (ver .env.example).
      apiBase: 'http://localhost:8000',
    },
  },

  compatibilityDate: '2026-08-19',

  typescript: {
    strict: true,
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'always-multiline',
        braceStyle: '1tbs',
      },
    },
  },

  supabase: {
    // url/key vêm de NUXT_PUBLIC_SUPABASE_URL / NUXT_PUBLIC_SUPABASE_KEY (publishable key).
    // SPA sem servidor: sessão em localStorage gerida pelo supabase-js (fluxo implícito);
    // nunca manipulamos tokens manualmente. Ver docs/adr/0003-auth-supabase-module-token-only.md.
    useSsrCookies: false,
    redirect: true,
    redirectOptions: {
      login: '/login',
      callback: '/confirm',
      exclude: ['/signup', '/confirm-email', '/forgot-password', '/reset-password'],
      saveRedirectToCookie: true,
    },
    // A SPA nunca consulta o Postgres diretamente (só a API REST) → sem tipos de banco.
    types: false,
  },
})
