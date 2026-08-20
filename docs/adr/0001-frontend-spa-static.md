# ADR-0001 — Front-end como SPA estática (Nuxt 4, `ssr: false`)

Data: 2026-08-19 · Status: aceito

## Contexto

O dashboard vive inteiramente atrás de login: todo dado vem da API FastAPI (`/api/v1/*`), que aceita **somente** `Authorization: Bearer <jwt do Supabase>` e tem CORS com lista explícita de origens e `allow_credentials=True` (sem wildcard, sem cookies). Não há páginas públicas indexáveis. A hospedagem ainda não está decidida (Caddy na VM Hostinger ou Vercel).

## Decisão

Nuxt 4 com `ssr: false` e `nuxt generate` → pasta estática (`.output/public`). Sem runtime Node em produção. Regras para manter a porta do SSR aberta: nenhum acesso a `window`/`localStorage` fora de `onMounted`/plugins `.client`; data layer em composables que não assumem browser; Lightweight Charts sempre em `.client.vue` + `<ClientOnly>`.

## Consequências

- Deploy = servir arquivos estáticos com fallback para `index.html`/`200.html` (um bloco no Caddyfile ou Vercel); zero processo para monitorar.
- A sessão Supabase existe só no navegador; nenhum token passa pelo servidor.
- Primeiro load baixa o bundle antes de renderizar (mitigado por code-splitting por rota e skeletons).
- Se surgir uma página pública (ex.: `/forecasts` aberto), migrar para híbrido via `routeRules` nessa rota — médio esforço, não bloqueante.
