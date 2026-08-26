# Handoff — o que o front-end ainda precisa do back-end (previsões) e roadmap do Monte Carlo

Data: 2026-08-26 · Público: agente do back-end · Origem: diagnóstico da integração front ↔ `GET /api/v1/forecasts`

## 1. Estado verificado em 26/08

| Camada | Estado | Evidência |
|---|---|---|
| API em produção | ✅ `GET /api/v1/forecasts` no ar (Railway, commit da PR #20) | sem token → 401; rota inexistente → 404; `openapi.json` publicado inclui a rota |
| Banco | ✅ `predictions` e `model_metrics` migradas, RLS `authenticated_select` | 224 linhas, 16 símbolos, horizontes 1–7, `is_fallback=false` |
| Rodada vigente | ⚠️ `20260824-local-drift` (run **local** de 24/08 14:33 UTC) | o job `ml-forecast` ainda não executou no Actions (agendamento das 00:05 de 26/08 foi anterior ao merge; nenhum `workflow_dispatch`) |
| Contrato | ✅ `openapi.json` + `openapi.d.ts` regenerados | job `openapi-types` verde |
| Front | ✅ ligado nesta etapa | `useForecasts()` consome a rota; Previsões e a faixa "Gap real × projeção" do Início renderizam a rodada |

## 2. O que o front mostra hoje e como mapeia a resposta

A resposta é uma lista plana `ForecastOut` (símbolo × alvo × horizonte). O front (`front-end/app/utils/forecast-mapping.ts`) deriva:

- **Diário** = horizonte 1 dia; **Semanal** = horizonte 7 dias; **Mensal e Anual = `—`** (o modelo não os publica — ADR-0004).
- **Variação %** = `predicted_close / preço atual (tickers 24h) − 1`; sem ticker, usa `expm1(predicted_log_return)` (relativo ao último fechamento observado pelo modelo).
- **Status da rodada** = `EM VALIDAÇÃO`, ou `FALLBACK NAIVE` quando `is_fallback=true`.
- **Arcos por horizonte** = média das variações por símbolo em 1 e 7 dias.
- **Gap real × projeção** (Início) = variação diária por ativo, ordenada por magnitude, só para ativos com preço atual.
- **Resumo da rodada** = texto determinístico montado com contagens e médias reais (nenhum número inventado).
- **MAE, acerto de direção e confiança = `—`** — os dados existem em `model_metrics`, mas nenhuma rota os expõe (item 3.1).
- **Monte Carlo = estado vazio honesto** — a API não devolve trajetórias (seção 4).

Regra que se mantém: o front **nunca** gera valor financeiro. Tudo que aparece é a resposta da API ou uma agregação aritmética dela.

## 3. O que ainda falta no back-end (ordem de prioridade)

### 3.1 Métricas da rodada vigente — `GET /api/v1/forecasts/metrics` (prioridade alta)

Preenche a faixa MODELO · MAE · DIREÇÃO e a coluna "Confiança" da tabela de cenários. Ler `model_metrics` da versão que assinou o run mais recente de `predictions`.

Campos necessários (schema Pydantic espelhando o jsonb já gravado):

- `model_version`, `model_type`, `trained_at`, `is_fallback`, `git_sha`
- `gate: { passed, reason }`
- `skill_score_h1`, `per_fold_skill_h1[]`
- `per_horizon: { y_1..y_7: { mae, rmse, dir_acc, n } }` — **MAE está em log-retorno (relativo), não em USDT**; expor com nome explícito (`mae_log_return`) e o front troca o rótulo para `MAE x,x %`. Não converter para USDT no back (não existe MAE em preço por símbolo global).
- `baseline_mae: { y_1..y_7 }` (naive) — permite o front mostrar skill por horizonte.
- `per_symbol: { SYMBOL: { mae, dir_acc, n } }` — base da coluna "Confiança". **Definir a métrica em uma linha de doc**: sugestão `confidence = round(dir_acc × 100)` no horizonte 1 (0–100), `null` para símbolo sem histórico suficiente. O front não inventa a definição; sem ela a coluna fica `—`.
- `realized_metrics` (nullable) — preenchido pelo job `ml-evaluate`; quando existir, o front passa a mostrar o realizado ao lado do validado.

Padrão: mesmo esqueleto de `controllers/forecasts.py` (auth via `get_claims`, repositório com client RLS, `[]`/`null` documentado quando não há rodada); testes offline em `tests/`.

### 3.2 Cabeçalho da rodada na própria lista (opcional, se 3.1 atrasar)

Alternativa mínima: incluir `model_type` em `ForecastOut`. Hoje o front exibe `GLOBAL · {model_version} · {status}` porque só tem `model_version`.

### 3.3 Resumo da rodada por LLM (baixa prioridade)

O front já mostra um resumo determinístico. Se quiser prosa, seguir o padrão de `insights_service.py` (global, cache por `model_version`, validação antes de gravar, números só da rodada). Não é bloqueio.

### 3.4 Operação (obrigatório para sair do run local)

1. Disparar `crypto_jobs.yml` com `job_to_run = ml-forecast` (`workflow_dispatch`) e confirmar no Actions que a imagem `crypto-ml` publica uma `model_version` com `git_sha` real.
2. Confirmar que o agendamento diário (00:05 UTC, após `feature-engineering-job`) executa nos dias seguintes.
3. Quando houver alvos realizados, rodar `ml-evaluate` uma vez para validar o preenchimento de `realized_metrics`.

### 3.5 Fechamento de contrato

Após qualquer rota/schema novo: `uv run python scripts/export_openapi.py ../front-end/openapi/openapi.json` → `pnpm api:types` no front → commitar os dois artefatos (CI `openapi-types`). Nunca editar `openapi.d.ts` à mão.

### 3.6 Fora deste handoff (já planejados separadamente)

- `last_seen_at` nas preferências + `GET /api/v1/insights/since` (deltas por usuário desde o último acesso) — plano próprio.
- Correções da leitura do dia (raciocínio vazado) — já entregues em `main` (commits `1ecf525` e `11e9c15`).

## 4. Roadmap — Monte Carlo

Contrato que o front já consome (`front-end/app/types/forecast.ts::MonteCarloSeries`):

```ts
{
  symbol: string
  horizonDays: number          // 7
  observed: { time: number /* s UTC */, value: number }[]   // histórico real até a linha de corte
  stepSeconds: number          // 86400
  paths: number[][]            // trajetórias REAIS simuladas; cada uma começa no passo 1 após o corte
  simulatedCount: number       // quantidade realmente simulada (a UI pode desenhar uma amostra)
  classified?: { best?: number, base?: number, worst?: number }   // índices em `paths`
}
```

Regras invioláveis (Design.md §11.3): o front só desenha trajetórias recebidas; `simulatedCount` é o número real; "Reiniciar simulação" apenas reanima, nunca re-simula.

### Fase 0 — agora
Sem endpoint. O front mantém o estado vazio. Nada a fazer.

### Fase 1 — simulação no job + endpoint de leitura (entrega mínima)

- **Onde simular:** no job `ml-forecast`, logo após publicar `predictions` — o modelo, os resíduos de validação e o último close já estão em memória.
- **Como:** bootstrap dos resíduos de validação por horizonte (coerente com `pred_lower/pred_upper`, que já são quantis desses resíduos) sobre o drift `predicted_log_return`; N = 1.000 trajetórias × 7 passos diários por símbolo; seed fixa por `model_version` (determinístico e reproduzível).
- **Persistência:** tabela `monte_carlo_runs (symbol, model_version, run_at, horizon_days, step_seconds, n_simulated, paths jsonb, classified jsonb)`, RLS `authenticated_select`, escrita só `service_role`; ~7 mil números por símbolo (≈50 KB) — cabe em jsonb; se pesar, Supabase Storage com ponteiro na linha.
- **Classificação no back:** `best`/`worst` = maior/menor valor terminal; `base` = trajetória mais próxima da mediana terminal. Gravar os índices em `classified` (o front respeita a classificação da API quando ela existe).
- **Endpoint:** `GET /api/v1/forecasts/monte-carlo?symbol=BTCUSDT` → `MonteCarloSeries`; `observed` = últimos 60 closes de `klines_1d` (velas fechadas); 404 documentado sem rodada.
- **Testes offline:** simulação determinística com seed; `classified` aponta para trajetórias existentes; nenhuma trajetória vazia; `len(paths) == n_simulated`.
- Fechar contrato (3.5). Front: trocar o corpo de `useMonteCarlo()` por `useAsyncData` — nenhum componente muda.

### Fase 2 — fidelidade
- Amostrar resíduos condicionados ao regime (volatilidade recente) em vez de i.i.d.
- Garantir que a faixa 10–90 % das trajetórias reproduz `pred_lower/pred_upper` (teste de consistência).
- Expor `realized` no endpoint quando o alvo já fechou, para o front desenhar o caminho real sobre a nuvem.

### Fase 3 — horizontes longos
Mensal/anual exigem outro modelo (ou agregação de regime); fora do escopo até um ADR próprio. Até lá, continuam `—` na UI.
