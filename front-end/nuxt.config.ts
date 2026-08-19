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
      title: 'crypto forecasting',
      htmlAttrs: { lang: 'pt-BR' },
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }],
      link: [{ rel: 'icon', href: '/favicon.ico' }],
    },
  },

  css: ['~/assets/css/main.css'],

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
