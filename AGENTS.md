# AGENTS.md

## Contexto do projeto

App de **forecasting de criptomoedas**. O projeto nasceu como um pipeline local de ingestão que consumia a API da Binance, tratava os dados e exportava Excel para análise EDA no Power BI. Essa base evoluiu para a plataforma atual: coleta automatizada com persistência em banco, feature engineering para modelos de ML, e (em construção) uma API REST com autenticação e um dashboard web.

### Stack e hospedagem

| Componente | Tecnologia | Hospedagem | Status |
| :--- | :--- | :--- | :--- |
| Pipeline de coleta | Python 3.13 + `uv`, Docker | GitHub Actions (cron) | **Em produção** |
| Feature engineering | Python (pandas, TA-Lib), Docker | GitHub Actions (diário, após coleta) | **Em produção** |
| Banco de dados | Supabase (PostgreSQL) | Supabase Cloud | **Em produção** |
| API REST | FastAPI (planejada) + autenticação | **VM** (não Render — docs antigas podem citar Render) | Planejada |
| ML / Forecasting | A definir (candidatos: Scikit-Learn, Prophet) | GitHub Actions / Runner | Planejado |
| Front-end | **Vue + Nuxt + Tailwind** (não React) | Domínio grátis da VM Hostinger **ou** Vercel — ainda não decidido | Planejado |

### Estado atual (2026-08)

Só o `back-end/` existe, ainda em construção. Não há API HTTP ainda: `back-end/main.py` é apenas um script de verificação de conectividade com a Binance. Os pontos de entrada reais são:

- `back-end/jobs.py` — dispatcher CLI dos jobs de ingestão (`five-minutes` → orderbook tickers, `hourly` → ticker 24h, `daily` → klines 15m/1h/1d; exit 0/1/2), rodando em Docker via `.github/workflows/crypto_jobs.yml` (com Cloudflare WARP para contornar geoblock da Binance). A lógica vive em `app/ingestion/`.
- `back-end/app/feature_engineering/main.py` — orquestrador do pipeline de features: calcula indicadores técnicos por timeframe (15m/1h/24h) conforme `app/feature_engineering/config/features.yml` e aplica a política de retenção.
- `back-end/historical_charge.py` — backfill histórico one-off de candles + recálculo de features.

### Arquitetura do back-end

Camadas (Clean Architecture / 3-Tier):

```
clients/       → conexões externas (BinanceClient com call_with_retry + erros tipados, Supabase)
services/      → transformação dos dados da Binance em DataFrames tipados (normalizador único de klines)
ingestion/     → jobs de ingestão: fetch no service + upsert no repository (erros propagam)
repositories/  → persistência pura no Supabase (klines, tickers, features, retenção)
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
```

Configuração via `.env` (Pydantic Settings em `back-end/config.py`, lazy via `get_settings()`): `SUPABASE_URL`, `SUPABASE_KEY`, `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `USE_TESTNET`, `BINANCE_PROXY` (opcional). Imports não têm side effects — env vars só são exigidas quando um componente conecta de fato; a suíte de testes roda offline sem `.env`.

Seams de injeção (preparação para FastAPI + Supabase Auth): `BaseRepository(supabase=None)`, `BinanceMarketService(client=None)`, `get_supabase_client(settings=None)` — controllers vão injetar um client Supabase por request carregando o JWT do usuário (RLS).

Modelo de acesso no Supabase (migrations em `back-end/supabase/migrations/`, aplicadas em 2026-08-19): RLS ativo nas 9 tabelas de `public`; policy `authenticated_select` (`for select to authenticated using (true)`) em todas; `anon` sem grants nem policies (deny); escrita e a RPC `clean_old_data` só para `service_role` (o `SUPABASE_KEY` dos jobs). Event trigger `ensure_rls` habilita RLS automaticamente em toda tabela nova — ela nasce deny-all até receber uma policy explícita.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on `gabriel-castro-dev/crypto-forecasting-app`, managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
