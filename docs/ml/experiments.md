# Log de experimentos — ML/Forecasting (marco 3)

Registro corrido das rodadas de experimento: configuração, seed, métricas e a decisão tomada.
Convenção: uma seção por experimento, id `EXP-{n}`; métricas sempre com skill score vs naive
(ver ADR-0004). Nada aqui é normativo — o que vale em produção é `app/ml/config/ml.yml`
e o `model_version` gravado em `model_metrics`.

## Decisões de setup (Fase 0 — 2026-08-23)

- Dependências do grupo `ml`: `torch 2.13.0+cpu` (índice pytorch-cpu), `lightgbm`, `scikit-learn 1.9`.
- `vectorbt` ficou **fora** do lock por ora: risco de incompatibilidade com o `pandas>=3.0`
  do projeto. Tentar na Fase 5 (backtest exploratório); se não resolver com pandas 3,
  a análise exploratória usa o motor próprio (`app/ml/backtest/engine.py`), que é o
  componente versionado de qualquer forma.
- Embargo entre splits fixado em 7 dias = max(horizons); invariante validada no loader
  (`app.ml.config.MLConfig`).

## Decisões de fechamento (Fase 8 — 2026-08-23)

- Backtest executa a posição no **close do sinal** (não há open de t+1 no dataset diário);
  o gap até a primeira execução real é modelado pelo `slippage_pct`. Documentado em
  `app/ml/backtest/engine.py`.
- Banda de incerteza = quantis 10/90% dos resíduos de validação do campeão, com largura
  forçada a não diminuir com o horizonte (cummin/cummax).
- Monitoramento recupera o close de origem da própria linha publicada
  (`origin = predicted_close × exp(−predicted_log_return)`) — sem consulta extra.
- Produção grava cada rodada em `model_metrics` (validação) e o job semanal preenche
  `realized_metrics`; este arquivo fica para experimentos manuais (tuning, novas features).

## Revisão de código (2026-08-23)

- Walk-forward de produção passou de holdout único para **4 folds** contíguos de 45 dias
  (expanding-window); candidatos, gate e bandas usam o pool dos folds e o skill por fold
  vai para `model_metrics.metrics.per_fold_skill_h1`.
- Linha de fallback em `model_metrics` grava as métricas do naive (o publicado), com o
  campeão reprovado e o ranking em `hyperparams`.
- Removidos: serialização do scaler (ADR-0004 não armazena artefatos), registry de
  baselines, split treino/val/teste fixo (só walk-forward), `get_model_metrics` sem uso.
- `predictions.horizon_days` restrito a 1–7 (migration `20260823230000`).
- O comando `backtest` anexa relatórios `BT-{data}` abaixo.

## Revisão Codex no PR #20 (2026-08-26)

- **Vela aberta (P1, confirmado no banco: 20 velas com `close_time > now()`):** a coleta
  diária às 00:05 UTC guarda a vela do dia corrente com minutos de negociação. Agora
  `build_dataset(..., as_of=run_date)` e `score_predictions(..., as_of=now)` descartam
  velas com `close_time > as_of` — origem da previsão, targets e realizações usam só
  velas fechadas. Efeito prático: a origem passa a ser a vela de ontem (fechada), e o
  h=1 volta a ser um dia de verdade.
- **Colisão de índices na inferência da GRU (P1):** origens vêm de `build_dataset` e o
  histórico da GRU de `finalize_training_frame` — RangeIndex distintos que colidem.
  `GRUModel.predict` agora carrega a identidade da linha pedida em coluna própria
  (`_requested`/`_origin`) com `ignore_index`, e exige índice único. Não havia
  disparado porque o campeão real é o drift.
- **Carteira equal-weight em log (P2):** média de log-retornos é a média geométrica;
  o motor agora agrega retornos simples por dia e volta a log só para o acumulado.
  Os relatórios `BT-*` anteriores a esta data subestimam levemente ROI/Sharpe.

## Experimentos

_(rodadas de produção ficam em `model_metrics`; registrar aqui experimentos manuais e os
relatórios `BT-*` do comando `backtest`)_

<!-- Template:
## EXP-1 — {descrição curta}
- Data: · Fase: · Seed:
- Config: {hiperparâmetros ou diff vs ml.yml}
- Validação (por horizonte h1/h4/h7): MAE ret · dir-acc · skill score
- Por símbolo (piores 3):
- Decisão: {segue / descarta / vira campeão}
-->

## BT-20260824 — backtest do campeão `drift` (validação)
- Data: 2026-08-24 · Treino: 2021-05-13 → 2026-08-17
- Ranking (skill h1 vs naive): drift +0.0020, ridge -0.0045, gru -0.0079, gbm -0.0261
- Skill h1 por fold: +0.0037, -0.0023, +0.0028, +0.0033
- Gate: Skill score 0.0020 em y_1 — publicação liberada.
- Estratégia long/flat: ROI -8.32% · Sharpe -0.77 · max drawdown -16.84% · 10 trades
- Buy-and-hold: ROI -3.08% · Sharpe 0.10 · max drawdown -27.77%
