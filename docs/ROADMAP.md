# Roadmap — próximos marcos

Quatro marcos **independentes** (qualquer ordem). Cada um será detalhado em plan mode na sua hora — isto é o overview do que o agente deve buscar: segurança, stack clara, arquitetura limpa. Antes de cada marco: ler `AGENTS.md` e as convenções em `docs/agents/`.

## 1. Front-end (dashboard) — ✅ v1 implementada (2026-08-19, branch `feat/front-end`)

Entregue: `front-end/` com auth completa, dashboard (candles + indicadores + resumo 24h), `/mercado`, estados, CI (`ci-front.yml`), ADRs 0001–0003 e `CONTEXT.md`. Pendências desta fase: smoke contra a API real com usuário de teste; decisão de hospedagem (marco 4); configurar Redirect URLs no Supabase Dashboard.

**Stack decidida:** Vue 3 + Nuxt 4 + Nuxt UI v4 (Tailwind v4) + Lightweight Charts v5, em `front-end/` na raiz do monorepo. Auth via `supabase-js` direto no Supabase Auth (login, signup, reset de senha, refresh de sessão); a API é consumida com o access token em `Authorization: Bearer`.

**Escopo:** telas de login/cadastro; dashboard com seletor de ativos (`/symbols`), gráfico de candles (`/klines`), overlay de indicadores (`/features`), tabela-resumo 24h (`/tickers/24h`).

**Atenção:** só a **publishable key** no client (nunca service_role/secret); CORS da API alinhado ao domínio final (`API_CORS_ORIGINS`); tokens nunca em localStorage manual (deixar o supabase-js gerenciar); estados de 401 → redirect para login. Skills úteis: `frontend-design`, `dataviz` (gráficos), `composition-patterns`.

## 2. UX & Usabilidade

**Escopo:** passada de UX sobre o front — onboarding, estados de loading/vazio/erro em todas as telas, responsividade mobile, acessibilidade (contraste, navegação por teclado, labels), feedbacks claros de auth (sem vazar se o e-mail existe), dark mode.

**Atenção:** mensagens de erro genéricas em falha de login (segurança); warm-up de indicadores (`null`s) precisa de tratamento visual, não tela quebrada; latência da API → skeletons. Skills úteis: `web-design-guidelines` (auditoria), `frontend-design`.

## 3. ML / Forecasting — ✅ v1 implementada (2026-08-23, branch `feat/front-end-v3`)

Entregue (ADR-0004; Prophet descartado): pacote `back-end/app/ml/` com dataset anti-leakage (split temporal por data + embargo, scaler train-only, features escala-invariantes), escada de candidatos (naive/drift/ridge → LightGBM → GRU) avaliada em walk-forward, gate de publicação vs naive com fallback marcado, backtest econômico com custos, tabelas `predictions`/`model_metrics` (RLS + `authenticated_select`, migration aplicada), `GET /api/v1/forecasts`, imagem `crypto-ml` + jobs no Actions (`ml-forecast` diário após o feature engineering; `ml-evaluate` semanal com alarme de degradação). Log de experimentos em `docs/ml/experiments.md`.

**Iterações futuras:** dados externos (sentimento, on-chain, macro — maior ganho segundo a literatura, exigem pipelines novos de coleta); timeframe `1h`; front consumindo `/forecasts` (curva + banda à direita da linha de corte).

## 4. Deploy em nuvem

**Escopo (revisado em 2026-08-23 — sem VM):** API no **Railway**, buildando `back-end/Dockerfile.api` a partir do repositório (Root Directory `back-end`, Watch Paths `/back-end/**`, config em `back-end/railway.json`); front estático na **Vercel**. As duas plataformas terminam TLS, então Caddy/nginx e o `deploy-api.yml` via SSH saem do escopo. Os jobs de coleta **permanecem no GitHub Actions**: a Binance geobloqueia IPs de nuvem (daí o WARP nos workflows) e a API não fala com a Binance em runtime. 

**Atenção:** secrets só nas variáveis do Railway/Vercel (nunca no git); `SUPABASE_KEY` service_role **não** vai para a API (só `SUPABASE_PUBLISHABLE_KEY`); a credencial do Firebase entra por `FIREBASE_CREDENTIALS_JSON`, nunca dentro da imagem; `API_CORS_ORIGINS` com o domínio da Vercel; adicionar esse domínio aos **domínios autorizados do Firebase** e às **redirect URLs do Supabase Auth**; healthcheck em `/health`; **backups do banco** (free tier do Supabase não tem backup automático — agendar `pg_dump` ou upgrade).
