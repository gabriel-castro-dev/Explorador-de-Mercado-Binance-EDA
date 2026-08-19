# ADR-0003 — Auth via `@nuxtjs/supabase` (sessão no navegador) e API token-only

Data: 2026-08-19 · Status: aceito

## Contexto

A API não emite tokens: valida localmente (JWKS ES256/RS256) o access token do Supabase Auth e consulta o banco com o JWT do usuário (RLS). O front precisa de login, cadastro com confirmação de e-mail, esqueci/redefinir senha, refresh de sessão e tratamento de 401 — sem nunca manipular tokens à mão nem expor a service_role.

## Decisão

- Módulo **`@nuxtjs/supabase` v2** com `useSsrCookies: false` (SPA sem servidor → supabase-js em localStorage, fluxo implícito), `redirect: true` (guard global para `/login`), `redirectOptions.callback = /confirm`, `saveRedirectToCookie` (volta para onde estava após login expirado). Só a **publishable key** chega ao cliente (`NUXT_PUBLIC_SUPABASE_KEY`).
- Cliente da API (`composables/useApi.ts`): injeta `Bearer` de `supabase.auth.getSession()`; em 401 tenta `refreshSession()` uma vez e repete; se ainda 401 → `signOut()`, `clearNuxtData()`, toast e `/login?reason=expired` (uma única expiração por vez).
- Mensagens de auth **genéricas** (nunca revelar se um e-mail existe) — textos exatos em `useAuthActions.ts` (`AUTH_COPY`), espelhando `docs/design/ux-spec.md §3`.
- Plugin `auth-hash.client.ts` (order −30) captura `#access_token&type=signup|recovery` antes do supabase-js limpar o hash, para `/confirm` e `/reset-password` saberem o tipo do link.

## Consequências

- Cookies não são usados; a API continua `allow_credentials` + Bearer. Mudar para SSR exigiria `useSsrCookies: true` + PKCE e revisão do guard.
- `useSupabaseUser()` devolve `JwtPayload` (claims), não `User` — usar `.email`/`.sub`.
- Configuração fora do repo (Supabase Dashboard): confirmação de e-mail ligada; Redirect URLs `http://localhost:3000/**` e a origem de produção; signing keys assimétricas (já recomendado no README).
