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
| **Back-end (API)** | FastAPI | Endpoints REST, autenticação via Supabase Auth, documentação Swagger e entrega de previsões. | VM | Em construção |
| **Machine Learning** | Scikit-Learn / Prophet (a definir) | Scripts de treinamento e geração de projeções diárias de preços. | GitHub Actions / Runner | Planejado |
| **Front-end** | Vue 3 + Nuxt + Tailwind | Dashboard interativo para comparação de ativos, gráficos temporais e performance dos modelos. | Domínio grátis da VM Hostinger ou Vercel (a definir) | Planejado |

---

## Tecnologias, Ferramentas & Padrões

* **Linguagem Base:** Python 3.13+
* **Gerenciador de Pacotes Python:** `uv` (Fast Python package installer & resolver)
* **Validação de Ambiente:** Pydantic Settings (carregamento lazy via `get_settings()` — imports sem side effects)
* **Arquitetura do Código (Back-end):** Clean Architecture / camadas (`clients`, `services`, `ingestion`, `repositories`, `feature_engineering`; `controllers` chegam com a API)
* **Front-end (planejado):** Vue 3, Nuxt e Tailwind CSS
* **Autenticação (planejada):** Controle de acesso à API e ao dashboard via Supabase Auth + RLS
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
* **CI:** `pytest` + `ruff` em todo PR/push à main; smoke build das imagens Docker quando Dockerfiles/dependências mudam.
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
│   │   ├── controllers/             # Rotas FastAPI + auth — próximo passo (em construção)
│   │   └── feature_engineering/     # Pipeline offline de features + retenção
│   │       ├── config/              # features.yml (features por timeframe + retenção)
│   │       ├── pipelines/           # Orquestração por fonte (klines, orderbook, ticker)
│   │       ├── transforms/          # Indicadores técnicos (SMA, RSI, Bollinger, ATR…)
│   │       └── retention/           # Limpeza programada por retenção
│   ├── tests/                       # Suíte pytest (offline, sem .env)
│   ├── jobs.py                      # Dispatcher CLI dos jobs de coleta
│   ├── historical_charge.py         # Backfill histórico de candles
│   ├── main.py                      # Script de verificação de conectividade com a Binance
│   ├── config.py                    # Settings Pydantic (get_settings lazy)
│   ├── Dockerfile.jobs              # Imagem dos jobs de coleta
│   ├── Dockerfile.feature-engineering
│   └── pyproject.toml               # Dependências via uv
├── docs/agents/                     # Convenções para agentes (issue tracker, labels, domínio)
├── front-end/                       # Dashboard (Vue/Nuxt) — planejado
└── ml_models/                       # Modelos preditivos e métricas — planejado
```

> `controllers/`, `front-end/` e `ml_models/` ainda não existem no repo — são os próximos marcos.

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
USE_TESTNET=True
```

### 4. Rodando os jobs localmente

```bash
uv run python jobs.py five-minutes   # orderbook tickers
uv run python jobs.py hourly         # ticker 24h
uv run python jobs.py daily          # klines 15m/1h/1d
uv run python -m app.feature_engineering.main   # features + retenção
```

### 5. Rodando a API localmente (em construção — próximo passo)

Quando os `controllers/` forem implementados:

```bash
uv run uvicorn app.main:app --reload
```

Documentação interativa (Swagger): http://127.0.0.1:8000/docs

# Licença

Este projeto está sendo desenvolvido como um portfólio avançado de Engenharia e Ciência de Dados, demonstrando habilidades com automação de infraestrutura, modelagem estatística e arquitetura escalável de software.
