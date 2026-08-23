# Plataforma de Engenharia de Dados, ML & Visualização - Mercado Binance

[![CI](https://github.com/gabriel-castro-dev/crypto-forecasting-app/actions/workflows/ci.yml/badge.svg)](https://github.com/gabriel-castro-dev/crypto-forecasting-app/actions/workflows/ci.yml)

Plataforma ponta a ponta (End-to-End) para coleta automatizada, armazenamento persistente, previsão de preços com Machine Learning e exibição de indicadores do mercado de criptomoedas através de dashboards interativos.

**Evolução do Projeto:** O sistema nasceu como um pipeline local de Análise Exploratória de Dados (EDA) focado em logs de terminal e planilhas CSV. A arquitetura atual transforma esse escopo inicial em um **monólito modular em monorepo**: jobs de coleta agendados, pipeline de feature engineering, uma API REST (em construção) e automação via CI/CD — responsabilidades separadas por camadas e contêineres, sem a complexidade operacional de microsserviços.

---

## Arquitetura do Sistema

O projeto adota o modelo de **Monorepo**, segregando responsabilidades desde a coleta até a entrega de valor na interface do usuário.

```
Binance API
│
▼
Jobs de Coleta (GitHub Actions: 5min / 1h / diário)
│
▼
Supabase (PostgreSQL + RLS)
│
├──────────────────────────────┐
▼                              ▼
FastAPI (REST API)           Machine Learning (Treinamento/Métricas)
│                              │
└──────────────┬───────────────┘
▼
Nuxt Dashboard (VM Hostinger ou Vercel)
│
▼
Usuário
```

### Divisão de Responsabilidades (Monorepo)

| Componente | Tecnologia | Papel no Ecossistema | Hospedagem | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Jobs de Coleta** | Python (`uv`) + Docker | Ingestão agendada (orderbook a cada 5min, ticker 24h a cada hora, klines diário) sem duplicidade no banco. | GitHub Actions | Em produção |
| **Feature Engineering** | Python (pandas, TA-Lib) + Docker | Cálculo diário de indicadores técnicos por timeframe + política de retenção. | GitHub Actions | Em produção |
| **Banco de Dados** | Supabase | PostgreSQL persistente com RLS para séries históricas, indicadores, previsões e versionamento de modelos. | Supabase Cloud | Em produção |
| **Back-end (API)** | FastAPI | Endpoints REST (klines, features, symbols, tickers 24h), autenticação via Supabase Auth (JWT/JWKS + RLS), Swagger. | VM | Em desenvolvimento (v1 pronta; deploy pendente) |
| **Machine Learning** | Scikit-Learn / Prophet (a definir) | Scripts de treinamento e geração de projeções diárias de preços. | GitHub Actions / Runner | Planejado |
| **Front-end** | Vue 3 + Nuxt 4 + Nuxt UI (Tailwind v4) + Lightweight Charts | Dashboard SPA: login/cadastro (Supabase Auth), gráfico de candles com indicadores, resumo 24h e tabela de mercado; consome a API com Bearer token. | Estático — Caddy na VM Hostinger ou Vercel (a definir) | Em desenvolvimento (v1 funcional; deploy pendente) |

---

## Tecnologias, Ferramentas & Padrões

* **Linguagem Base:** Python 3.13+
* **Gerenciador de Pacotes Python:** `uv` (Fast Python package installer & resolver)
* **Validação de Ambiente:** Pydantic Settings (carregamento lazy via `get_settings()` — imports sem side effects)
* **Arquitetura do Código (Back-end):** Clean Architecture / camadas (`clients`, `services`, `ingestion`, `repositories`, `feature_engineering`; `controllers` chegam com a API)
* **Front-end:** Vue 3 + Nuxt 4 (SPA estática, `ssr: false`), Nuxt UI v4 / Tailwind v4, TradingView Lightweight Charts v5, `@nuxtjs/supabase`, `openapi-fetch` com tipos gerados do OpenAPI (`pnpm api:types`), Vitest + ESLint + vue-tsc
* **Autenticação:** Supabase Auth no front (supabase-js gerencia a sessão) → `Authorization: Bearer` na API → JWT validado via JWKS → RLS no banco
* **Design Patterns:** Retry Pattern centralizado (`call_with_retry` com erros tipados) e Injeção de Dependências (seams para testes offline e para o `Depends()` do FastAPI)
* **Qualidade:** `pytest` (suíte 100% offline, sem `.env`) + `ruff` (lint e format) no CI

---

## Funcionalidades da Plataforma

### Ingestão & Pipeline de Dados
* **Atualização Automática (Cron):** Coleta em três cadências via GitHub Actions (5min / horária / diária) com upsert idempotente — sem duplicidade no banco.
* **Resiliência a Falhas:** Retry centralizado com classificação de erros da API da Binance (permissão, símbolo inválido) e recuperação de streams históricos a partir do último candle.
* **Data Quality:** Validação de tipos e consistência estrutural antes da inserção no banco PostgreSQL; falhas de ingestão derrubam o job com exit code ≠ 0 (visível no CI).
* **Retenção Programada:** Limpeza automática por tabela conforme política declarada em YAML (ex.: klines 15m por 7 dias, features 24h permanentes).

### Inteligência Artificial & Computação
* **Predição de Séries Temporais:** Modelos estatísticos/ML atualizados periodicamente utilizando todo o histórico de dados limpos. *(planejado)*
* **Versionamento:** Rastreabilidade completa de métricas de performance (MAE, RMSE) por versão de modelo gerado. *(planejado)*

### Entrega de Dados (API REST — em construção)
* **Endpoints REST:** Rotas para histórico de preços, indicadores e previsões futuras.
* **Segurança:** RLS ativo em todas as tabelas (leitura só para usuários autenticados; escrita restrita aos jobs via service role).
* **Documentação Viva:** Swagger e OpenAPI gerados dinamicamente para consumo facilitado.

### CI/CD
* **CI (back-end):** `pytest` + `ruff` em todo PR/push à main; smoke build das imagens Docker quando Dockerfiles/dependências mudam.
* **CI (front-end):** `ci-front.yml` — ESLint, `nuxt typecheck`, Vitest e `nuxt generate` (artefato estático); job `openapi-types` reexporta o OpenAPI do back-end e falha se `front-end/openapi/openapi.json` / `app/types/openapi.d.ts` estiverem desatualizados.
* **CD:** Push na main publica as imagens no GHCR (`crypto-jobs`, `crypto-feature-engineering`); os crons de coleta apenas fazem `docker pull` da imagem pronta.

---

## Schema do Banco de Dados (Supabase / PostgreSQL)

```
┌─────────────────────────────────────────────────────────────────┐
│ symbols (tabela referencial)                                    │
│ ├─ PK symbol: text                                              │
│ └─ created_at: timestamptz                                      │
└──────┬──────────────────────────────────────────────────────────┘
       │ FK
       ├──────────────────────────────────────────────────────┐
       │                                                      │
       ▼                                                      ▼
┌─────────────────────────────────────┐    ┌──────────────────────────────────────┐
│ klines_15m / klines_1h / klines_1d  │    │ ticker_24hr_history                  │
│ (OHLCV bruto — top 20 ativos)       │    │ (24h summary — todos os ativos)      │
├─────────────────────────────────────┤    ├──────────────────────────────────────┤
│ PK id: bigint                       │    │ PK id: bigint                        │
│ symbol: text FK                     │    │ symbol: text FK                      │
│ open_time / close_time: timestamp   │    │ open_time / close_time: timestamp    │
│ open / high / low / close: numeric  │    │ price_change / price_change_percent  │
│ volume: numeric                     │    │ weighted_avg_price / prev_close_price│
│ quote_asset_volume: numeric         │    │ last_price / last_qty                │
│ number_of_trades: integer           │    │ bid_price -> ask_qty                 │
│ taker_buy_*: numeric                │    │ open_price -> low_price              │
└─────────────────────────────────────┘    │ volume / quote_volume                │
                                           │ first_id / last_id / count           │
┌─────────────────────────────────────┐    └──────────────────────────────────────┘
│ orderbook_tickers                   │    
│ (bid/ask — top 20 ativos, 5min)     │    ┌─────────────────────────────────────────────────────────┐
├─────────────────────────────────────┤    │ features_15m / features_1h / features_24h               │
│ PK id: bigint                       │    │ (indicadores calculados por time-frame — top 20)        │
│ symbol: text FK                     │    ├─────────────────────────────────────────────────────────┤
│ bid_price / bid_qty: numeric        │    │ PK (symbol, timestamp)                                  │
│ ask_price / ask_qty: numeric        │    │ symbol: text FK                                         │
│ fetched_at: timestamptz             │    │ timestamp: timestamptz                                  │
└─────────────────────────────────────┘    │ sma_20 / sma_50 / sma_200: float8                       │
                                           │ ema_12 / ema_26: float8                                 │
                                           │ rsi_14: float8                                          │
                                           │ macd: float8 (GENERATED)                                │
                                           │ macd_signal: float8                                     │
                                           │ macd_histogram: float8 (GENERATED)                      │
                                           │ avg_price_deviation_sma20/50/200: float8                │
                                           │ bb_upper / bb_middle / bb_lower: float8                 │
                                           │ bb_width: float8 (GENERATED)                            │
                                           │ atr_14: float8                                          │
                                           │ bid_ask_spread / order_imbalance: float8                │
                                           │ price_change_percent / volume_change_24h: float8        │
                                           │ volume_sma_20: float8                                   │
                                           └─────────────────────────────────────────────────────────┘
```

> Coleta restrita ao **top 20 ativos por volume 24h** (exceto `ticker_24hr_history`, que coleta todos para rankear). As tabelas `features_*` armazenam indicadores calculados a partir dos dados brutos — são a entrada dos modelos de ML. Todas as tabelas têm **RLS ativo**: leitura para usuários autenticados, escrita apenas via service role dos jobs.

---

## Estrutura do Monorepo

```text
crypto-forecasting-app/
├── .github/workflows/
│   ├── ci.yml                       # CI: pytest + ruff + smoke build Docker
│   ├── publish-images.yml           # CD: publica imagens no GHCR
│   └── crypto_jobs.yml              # Crons de coleta (5min/1h/diário) + feature engineering
├── back-end/
│   ├── app/
│   │   ├── clients/                 # Conexões externas (Binance com retry, Supabase)
│   │   ├── services/                # Transformação dos dados da Binance em DataFrames tipados
│   │   ├── ingestion/               # Jobs de ingestão: fetch no service + upsert no repository
│   │   ├── repositories/            # Persistência pura no Supabase
│   │   ├── controllers/             # Rotas FastAPI (klines, features, symbols, tickers) + deps de auth/RLS
│   │   ├── auth/                    # Verificação local de JWT do Supabase (JWKS)
│   │   ├── schemas/                 # Response models Pydantic
│   │   ├── core/                    # Vocabulário compartilhado (Timeframe)
│   │   └── feature_engineering/     # Pipeline offline de features + retenção
│   │       ├── config/              # features.yml (features por timeframe + retenção)
│   │       ├── pipelines/           # Orquestração por fonte (klines, orderbook, ticker)
│   │       ├── transforms/          # Indicadores técnicos (SMA, RSI, Bollinger, ATR…)
│   │       └── retention/           # Limpeza programada por retenção
│   ├── tests/                       # Suíte pytest (offline, sem .env)
│   ├── jobs.py                      # Dispatcher CLI dos jobs de coleta
│   ├── backfill_features.py         # Backfill histórico em memória (persiste só features)
│   ├── main.py                      # Script de verificação de conectividade com a Binance
│   ├── config.py                    # Settings Pydantic (get_settings lazy)
│   ├── Dockerfile.jobs              # Imagem dos jobs de coleta
│   ├── Dockerfile.feature-engineering
│   └── pyproject.toml               # Dependências via uv
├── docs/
│   ├── agents/                      # Convenções para agentes (issue tracker, labels, domínio)
│   └── adr/                         # Decisões de arquitetura (ADRs)
├── CONTEXT.md                       # Glossário do domínio (timeframe, kline, feature, warm-up…)
├── front-end/                       # Dashboard Nuxt 4 (SPA estática)
│   ├── app/
│   │   ├── pages/                   # login, signup, confirm-email, confirm, forgot/reset-password, index (dashboard), mercado
│   │   ├── layouts/                 # auth (card) · default (header, nav, barra inferior mobile)
│   │   ├── components/              # SymbolSelector, TimeframeToggle, SnapshotBadge, chart/*, IndicatorToggles, Summary24hStrip, Tickers24hTable…
│   │   ├── composables/             # useApi (Bearer + 401→refresh→retry), useMarketData, useDashboardQuery, useIndicatorPrefs, useFreshness, useAuthActions
│   │   ├── utils/                   # formatação pt-BR/UTC, erros da API, mapping para o gráfico, tickers, constantes dos indicadores
│   │   ├── types/                   # openapi.d.ts (GERADO) + aliases
│   │   ├── middleware/ · plugins/   # guest; captura do hash de auth
│   │   └── assets/css/main.css      # tokens de design (light/dark)
│   ├── openapi/openapi.json         # schema exportado do back-end (input do codegen)
│   ├── test/unit/                   # Vitest (utils, cliente da API)
│   └── nuxt.config.ts · package.json · .env.example
└── ml_models/                       # Modelos preditivos e métricas — planejado
```

> `ml_models/` ainda não existe no repo — é o próximo marco.

## Instalação & Setup de Desenvolvimento

Pré-requisitos:

* Python 3.13+ instalado.
* Gerenciador `uv` instalado (`pip install uv`).

### 1. Preparando o Back-end

```bash
cd back-end
uv sync   # instala dependências e cria o ambiente virtual
```

### 2. Rodando os testes

A suíte é 100% offline — não precisa de `.env` nem de credenciais:

```bash
uv run pytest
uv run ruff check .
```

### 3. Variáveis de Ambiente (para rodar os jobs de verdade)

Crie um arquivo `.env` dentro de `back-end/`:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-service-role-key
BINANCE_API_KEY=sua-api-key-da-binance
BINANCE_API_SECRET=seu-secret-da-binance

# Preferências do usuário (Firestore) — só a API precisa disso
FIREBASE_CREDENTIALS_PATH=./crypto-forecasting-preferences-firebase-adminsdk-XXXX.json
```

> A credencial do Firebase **nunca** vai para o git (coberta pelo `.gitignore`)
> nem para dentro da imagem Docker. No container, monte o arquivo como volume
> read-only ou passe o conteúdo do JSON em `FIREBASE_CREDENTIALS_JSON`.

> Os dados de mercado vêm da Binance **real** por padrão (endpoints públicos —
> as chaves não precisam de permissões especiais). `USE_TESTNET=True` existe
> como opção, mas a testnet guarda ~2 semanas de histórico sintético e não
> serve para o dataset de treino.

### 4. Rodando os jobs localmente

```bash
uv run python jobs.py five-minutes   # orderbook tickers
uv run python jobs.py hourly         # ticker 24h
uv run python jobs.py daily          # klines 15m/1h/1d
uv run python -m app.feature_engineering.main   # features + retenção
```

#### Backfill histórico (one-off)

Popula anos de features calculadas **em memória** a partir da Binance — só as
features entram no banco (klines cruas apenas em `klines_1d`, permanente, que
guarda o preço usado como target do ML). O warm-up dos indicadores (300 barras
extras) é buscado e descartado automaticamente: nenhuma linha com `sma_200`
nulo é gravada. A lista de símbolos vive em
`app/feature_engineering/config/symbols.yml`.

```bash
uv run python backfill_features.py --timeframe 1d              # 5 anos
uv run python backfill_features.py --timeframe 1h              # 720 dias
uv run python backfill_features.py --timeframe 15m             # 175 dias
uv run python backfill_features.py --timeframe 1d --symbols BTCUSDT  # retomar um símbolo
```

Os horizontes padrão cabem nas janelas de retenção e no free tier do Supabase
(~240 MB no total para 20 símbolos).

### 5. Rodando a API localmente

Além do `.env` dos jobs, a API precisa de:

```env
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...   # ou a anon key legada — NUNCA a service_role
# SUPABASE_JWT_SECRET=...                     # só se o projeto ainda usa HS256 legado
# API_CORS_ORIGINS=http://localhost:3000      # origens do front, separadas por vírgula
```

```bash
uv run fastapi dev   # entrypoint app.main:app declarado no pyproject
```

Documentação interativa (Swagger): http://127.0.0.1:8000/docs

Auth: o front autentica direto no Supabase Auth (supabase-js) e envia o access token
em `Authorization: Bearer <jwt>`; a API valida o token localmente via JWKS e consulta
o banco com o token do usuário — o RLS decide as linhas. Recomendado ativar signing
keys assimétricas: Dashboard → Settings → JWT Signing Keys → "Migrate JWT secret" →
"Rotate keys" (revogar o secret legado ~1h depois).

### 6. Rodando o front-end (dashboard)

Pré-requisitos: Node 24 LTS + pnpm (`npm i -g pnpm`).

```bash
cd front-end
cp .env.example .env      # NUXT_PUBLIC_SUPABASE_URL, NUXT_PUBLIC_SUPABASE_KEY (publishable!), NUXT_PUBLIC_API_BASE
pnpm install
pnpm dev                  # http://localhost:3000 (a API precisa estar em NUXT_PUBLIC_API_BASE e liberar essa origem em API_CORS_ORIGINS)
```

Qualidade e build:

```bash
pnpm lint && pnpm typecheck && pnpm test   # ESLint · vue-tsc · Vitest
pnpm generate                              # SPA estática em .output/public (servir com fallback para index.html/200.html)
```

Tipos da API são gerados do OpenAPI do back-end e commitados (o CI falha se ficarem para trás):

```bash
cd back-end && uv run python scripts/export_openapi.py ../front-end/openapi/openapi.json
cd ../front-end && pnpm api:types
```

Supabase Dashboard (Authentication → URL Configuration): adicionar `http://localhost:3000/**` e a origem de produção em **Redirect URLs** (links de confirmação de e-mail e de redefinição de senha voltam para `/confirm` e `/reset-password`).

---

## Referência da API (v1)

Todas as rotas de dados exigem `Authorization: Bearer <access_token>` (401 sem token).
Documentação interativa completa: `/docs` (Swagger) e `/redoc` com a API rodando.

| Método | Rota | Descrição | Parâmetros |
| :--- | :--- | :--- | :--- |
| GET | `/health` | Liveness (público, sem banco) | — |
| GET | `/api/v1/symbols` | Ativos rastreados | — |
| GET | `/api/v1/klines/{timeframe}` | Candles OHLCV, mais recente primeiro | path: `15m`\|`1h`\|`1d` · query: `symbol` (obrigatório), `limit` (1-1000, padrão 200), `start`/`end` (ISO 8601) |
| GET | `/api/v1/features/{timeframe}` | Indicadores técnicos calculados | idem klines; `24h` é aceito como sinônimo de `1d` |
| GET | `/api/v1/tickers/24h` | Snapshot 24h mais recente por ativo | query: `symbol` (opcional) |
| GET | `/api/v1/preferences` | Preferências do usuário autenticado (padrões se nunca salvou) | — |
| PUT | `/api/v1/preferences` | Salva as preferências (idempotente) | corpo: `display_name`, `phone` (E.164), `notifications`, `chart` |
| POST | `/api/v1/auth/firebase-token` | Custom token do Firebase para o usuário autenticado | — |

### Identidade: um cadastro, dois sistemas

O usuário se cadastra **uma vez**, no Supabase Auth — que continua sendo a única
autoridade sobre a senha. A conta espelho no Firebase é criada automaticamente na
primeira requisição autenticada (`GET /api/v1/preferences`), **sem senha** e com o
mesmo id do Supabase (`sub` → `uid`). Login por senha direto no Firebase falha por
construção, então as credenciais nunca divergem entre os dois sistemas.

Quando o cliente precisar de uma sessão Firebase (por exemplo, para falar direto com
o Firestore no futuro), o fluxo é:

```
front → POST /api/v1/auth/firebase-token   (com o Bearer do Supabase)
     ← { "custom_token": "...", "expires_in": 3600 }
front → POST identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=<apiKey do app Web>
     ← { "idToken": "...", ... }
```

A `apiKey` do app Web é pública (vai no navegador) e **não** dá acesso a dado nenhum
sozinha — quem autoriza é o custom token, emitido só para o dono de um JWT válido.

### Regras do Firestore

O `firestore.rules` nega todo acesso de cliente: só a API (Admin SDK) fala com o
Firestore, então a autorização acontece na API. Para publicar e conferir:

```bash
firebase deploy --only firestore:rules        # publica o que está no repo
uv run python scripts/check_firestore_rules.py <chave-admin>.json   # confere publicado == repo
```

A conferência é tarefa administrativa: ler regras exige `firebaserules.viewer`, papel
que a service account de runtime da API **não** tem de propósito (ela carrega apenas
`datastore.user` e `firebaseauth.admin`). Rodar sem argumento usa a credencial do
`.env` e falha com uma mensagem explicando isso.

### Obtendo um access token sem o front-end

Para testar a API sem o dashboard (curl/Swagger), autentique um usuário direto no Supabase Auth:

```bash
curl -s -X POST "https://<projeto>.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "teste@exemplo.com", "password": "sua-senha"}'
# → {"access_token": "eyJ...", "expires_in": 3600, ...}
```

### Exemplos

```bash
TOKEN="eyJ..."   # access_token acima

curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/v1/klines/1h?symbol=BTCUSDT&limit=2"
```

```json
[
  {
    "symbol": "BTCUSDT",
    "open_time": "2026-08-19T14:00:00+00:00",
    "open": 113250.1, "high": 113900.0, "low": 112800.5, "close": 113512.3,
    "volume": 1284.52,
    "close_time": "2026-08-19T14:59:59.999000+00:00",
    "quote_asset_volume": 145630021.4,
    "number_of_trades": 183220,
    "taker_buy_base_asset_volume": 640.1,
    "taker_buy_quote_asset_volume": 72701123.9
  }
]
```

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/v1/features/1d?symbol=BTCUSDT&limit=1"
# → [{"symbol": "BTCUSDT", "timestamp": "...", "sma_20": ..., "rsi_14": ..., "macd": ..., ...}]
```

Comportamentos: histórico vazio → `200 []` · timeframe inválido → `422` · token ausente/expirado → `401` com `WWW-Authenticate: Bearer` · indicadores podem vir `null` nas janelas de warm-up (ex.: `sma_200` nas primeiras 200 velas).

# Licença

Este projeto está sendo desenvolvido como um portfólio avançado de Engenharia e Ciência de Dados, demonstrando habilidades com automação de infraestrutura, modelagem estatística e arquitetura escalável de software.
