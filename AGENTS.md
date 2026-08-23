# AGENTS.md

## Contexto do projeto

App de **forecasting de criptomoedas**. O projeto nasceu como um pipeline local de ingestão que consumia a API da Binance, tratava os dados e exportava Excel para análise EDA no Power BI. Essa base evoluiu para a plataforma atual: coleta automatizada com persistência em banco, feature engineering para modelos de ML, e (em construção) uma API REST com autenticação e um dashboard web.

### Stack e hospedagem

| Componente | Tecnologia | Hospedagem | Status |
| :--- | :--- | :--- | :--- |
| Pipeline de coleta | Python 3.13 + `uv`, Docker | GitHub Actions (cron) | **Em produção** |
| Feature engineering | Python (pandas, TA-Lib), Docker | GitHub Actions (diário, após coleta) | **Em produção** |
| Banco de dados | Supabase (PostgreSQL) | Supabase Cloud | **Em produção** |
| API REST | FastAPI + Supabase Auth (JWT/JWKS, RLS) | **Railway** (container do GHCR; decisão de 2026-08-23 — docs antigas citam VM/Render) | v1 implementada; deploy em configuração |
| Preferências do usuário | Firestore via Firebase Admin SDK | Firebase (plano Spark) | **Em produção** |
| ML / Forecasting | A definir (candidatos: Scikit-Learn, Prophet) | GitHub Actions / Runner | Planejado |
| Front-end | **Vue 3 + Nuxt 4 (SPA estática) + Nuxt UI v4/Tailwind v4 + Lightweight Charts v5** (não React) | **Vercel** (estático) | v1 funcional em `front-end/`; deploy pendente |

### Estado atual (2026-08)

`back-end/` (jobs, features, API FastAPI v1) e `front-end/` (dashboard Nuxt) existem. `back-end/main.py` é apenas um script de verificação de conectividade com a Binance; a API é `back-end/app/main.py`. Os pontos de entrada reais são:

- `back-end/jobs.py` — dispatcher CLI dos jobs de ingestão (`five-minutes` → orderbook tickers, `hourly` → ticker 24h, `daily` → klines 15m/1h/1d; exit 0/1/2), rodando em Docker via `.github/workflows/crypto_jobs.yml` (com Cloudflare WARP para contornar geoblock da Binance). A lógica vive em `app/ingestion/`.
- `back-end/app/feature_engineering/main.py` — orquestrador do pipeline de features: calcula indicadores técnicos por timeframe (15m/1h/24h) conforme `app/feature_engineering/config/features.yml` e aplica a política de retenção.
- `back-end/backfill_features.py` — backfill histórico em memória: busca klines da Binance por símbolo, calcula as features e persiste **só as features** (klines cruas apenas em `klines_1d`, que é permanente e guarda o target do ML). CLI: `--timeframe {15m,1h,1d}`, `--start-days`, `--symbols`. A lista fixa de símbolos vive em `back-end/app/feature_engineering/config/symbols.yml`.

### Arquitetura do back-end

Camadas (Clean Architecture / 3-Tier):

```
main.py        → app FastAPI (create_app: CORS, routers, /health público)
controllers/   → rotas /api/v1 (symbols, klines/{tf}, features/{tf}, tickers/24h, preferences, auth) + deps.py
                 (HTTPBearer → get_claims → client Supabase por request com JWT do usuário → RLS)
auth/          → verificação local de JWT do Supabase Auth (JWKS ES256/RS256, fallback HS256 opcional)
schemas/       → response models Pydantic (extra="ignore", indicadores nullable)
core/          → Timeframe (vocabulário único 15m/1h/1d, alias 24h, nomes de tabela)
clients/       → conexões externas (BinanceClient com call_with_retry + erros tipados, Supabase)
  └─ firebase/     → Firebase Admin SDK / Firestore (preferências do usuário; init lazy e idempotente)
services/      → transformação dos dados da Binance em DataFrames tipados (normalizador único de klines)
                 + firebase_identity.py (conta espelho no Firebase: uid = sub do Supabase, sem senha; custom token)
ingestion/     → jobs de ingestão: fetch no service + upsert no repository (erros propagam)
repositories/  → persistência pura no Supabase (klines, tickers, features, retenção)
                 + preferences_repository.py (Firestore: 1 doc por usuário, id = claims.sub)
feature_engineering/
  ├─ pipelines/    → orquestração por fonte (klines, orderbook, ticker_24hr)
  ├─ transforms/   → indicadores técnicos via registry (SMA, EMA, RSI, Bollinger, ATR…)
  ├─ downsample/   → resample 5min→1h, 1h→1d
  ├─ retention/    → limpeza programada por tabela
  └─ config/features.yml → features por timeframe + política de retenção
```

Fluxo de dados: Binance API → jobs de coleta → tabelas brutas no Supabase (`klines_*`, `ticker_24hr_history`, `orderbook_tickers`) → feature engineering → tabelas `features_*` (entrada dos modelos de ML). Coleta restrita ao top 20 ativos por volume 24h (exceto `ticker_24hr_history`).

### Comandos

```bash
cd back-end
uv sync                              # instalar dependências
uv run pytest                        # rodar testes
uv run python jobs.py daily          # rodar um job de ingestão localmente
uv run python -m app.feature_engineering.main   # pipeline de features
uv run fastapi dev                   # API (exige SUPABASE_PUBLISHABLE_KEY no .env)
```

Configuração via `.env` (Pydantic Settings em `back-end/config.py`, lazy via `get_settings()`): `SUPABASE_URL`, `SUPABASE_KEY`, `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `USE_TESTNET`, `BINANCE_PROXY` (opcional). Imports não têm side effects — env vars só são exigidas quando um componente conecta de fato; a suíte de testes roda offline sem `.env`.

Seams de injeção (preparação para FastAPI + Supabase Auth): `BaseRepository(supabase=None)`, `BinanceMarketService(client=None)`, `get_supabase_client(settings=None)` — controllers vão injetar um client Supabase por request carregando o JWT do usuário (RLS).

Modelo de acesso no Supabase (migrations em `back-end/supabase/migrations/`, aplicadas em 2026-08-19): RLS ativo nas 9 tabelas de `public`; policy `authenticated_select` (`for select to authenticated using (true)`) em todas; `anon` sem grants nem policies (deny); escrita e a RPC `clean_old_data` só para `service_role` (o `SUPABASE_KEY` dos jobs). Event trigger `ensure_rls` habilita RLS automaticamente em toda tabela nova — ela nasce deny-all até receber uma policy explícita.

### Arquitetura do front-end (`front-end/`, Nuxt 4 — diretório `app/`)

SPA estática (`ssr: false`; ADR-0001): nenhum dado é pré-renderizado; a sessão Supabase vive só no navegador (supabase-js, fluxo implícito, `@nuxtjs/supabase` com `useSsrCookies: false`); a API recebe `Authorization: Bearer` (ADR-0003). Regra: nada de `window`/`localStorage` fora de `onMounted`/plugins `.client` (preserva migração futura para híbrido).

```
app/
  pages/        login · signup · confirm-email · confirm (callback) · forgot-password · reset-password · index (dashboard) · mercado
  layouts/      auth (card) · default (header + nav + barra inferior mobile)
  middleware/   guest (logado → /); o guard global vem do módulo supabase (redirectOptions)
  plugins/      auth-hash.client (captura #access_token&type= antes do supabase-js limpar o hash)
  composables/  useApi (openapi-fetch tipado; 401 → refreshSession → retry → signOut + /login?reason=expired)
                useMarketData (useSymbols/useKlines/useFeatures/useTickers24h via useAsyncData com chave reativa)
                useDashboardQuery (symbol/tf na URL) · useIndicatorPrefs (localStorage) · useFreshness (selo fresh/stale)
                useAuthActions (mensagens genéricas da ux-spec) · useUiState
  components/   SymbolSelector · TimeframeToggle · SnapshotBadge · chart/{ChartPanel,CandlestickChart.client,ChartSwatch}
                IndicatorToggles · Summary24hStrip · Tickers24hTable · MarketListMobile · EmptyState/ErrorState/ChartSkeleton · auth/*
  utils/        constants (timeframes, INDICATOR_DEFS com cores/traços) · format (pt-BR, UTC, "há X") · api-errors · chart-mapping · tickers
  types/        openapi.d.ts (GERADO por `pnpm api:types` — nunca editar) · api.ts (aliases Kline, FeatureRow, Ticker24h…)
  assets/css/   main.css — tokens de design light/dark (docs/design/tokens.md), utilitários num/eyebrow/text-up/text-down
```

Contrato da API: `front-end/openapi/openapi.json` é exportado por `back-end/scripts/export_openapi.py`; o job `openapi-types` do CI falha se o JSON ou `openapi.d.ts` ficarem para trás. Respostas são newest-first (o mapping reverte), indicadores `null` viram gaps (`WhitespaceData`), `detail` é string no 401 e array no 422, 5xx é texto — tudo normalizado em `utils/api-errors.ts`.

Comandos: `cd front-end && pnpm install && pnpm dev` (precisa de `.env` — ver `.env.example`; só a **publishable key**); `pnpm lint && pnpm typecheck && pnpm test`; `pnpm generate` (estático em `.output/public`). Gráfico: Lightweight Charts v5 (`addSeries`, panes via `paneIndex`, `setStretchFactor`), sempre client-only (`.client.vue` + `<ClientOnly>`).

### Roadmap

Próximos marcos (front-end, UX, ML, deploy) em [docs/ROADMAP.md](docs/ROADMAP.md) — passos independentes, detalhar em plan mode na hora de cada um.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `gabriel-castro-dev/crypto-forecasting-app`, managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
