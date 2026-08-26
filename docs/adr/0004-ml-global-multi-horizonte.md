# ADR-0004 — Forecasting: modelo global multi-horizonte com escada empírica (Prophet descartado)

Data: 2026-08-23 · Status: aceito

## Contexto

O marco 3 (ML/Forecasting) previa "Prophet / sklearn a definir". Prophet é um modelo univariado de tendência+sazonalidade: não consome as features já construídas (`features_24h`), assume padrões sazonais estáveis que séries de cripto não têm e não modela a dependência não-linear que justifica o pipeline de feature engineering. A decisão de arquitetura foi guiada pela revisão sistemática de Ataei et al. (2025), *Applications of Deep Learning to Cryptocurrency Trading* (Soft Comput. Fusion Appl. 2(4), 255–268; 75 papers, 2020–2025): RNNs (LSTM/GRU) e híbridos/ensembles superam métodos clássicos, mas os ganhos são incrementais, séries de cripto beiram random walk, e backtests sem custos enganam.

Restrições do sistema: dados diários (~5 anos em `features_24h`/`klines_1d`, permanentes; 20 símbolos congelados, alguns recém-listados), treino em runners CPU do GitHub Actions, cadência de previsão diária (~00:05 UTC, após o feature engineering), suíte de testes 100% offline.

## Decisão

- **Target:** log-retorno diário (`y_h = log(close_{t+h}/close_t)`), não preço — retornos são ~estacionários e evitam o colapso em "prever o preço de ontem". Preço é reconstruído só para exibição; direção deriva do sinal.
- **Horizonte:** multi-output 1–7 dias, com banda de incerteza (quantis do erro de validação) alargando com o horizonte — alimenta a curva reservada no gráfico do front.
- **Escopo:** um **modelo global multi-símbolo** (embedding de símbolo no DL, categórico no LightGBM): ~36k amostras vs ~1,8k por símbolo — melhor troca viés/variância com histórico curto.
- **Escada empírica**, não aposta em arquitetura: baselines (naive random-walk, drift, ridge) → LightGBM global → GRU (PyTorch); ensemble só se ≥2 candidatos batem o naive. A métrica central é o **skill score vs naive** (`1 − MAE_modelo/MAE_naive`); RMSE isolado não decide nada.
- **Gate de publicação:** o campeão só publica previsões se bater o naive na validação; caso contrário o job publica o fallback naive marcado (`is_fallback`) — o dashboard nunca fica sem curva, e a degradação fica visível.
- **Operação:** retreino diário no próprio job de inferência (dataset pequeno → minutos em CPU; seed fixa), sem armazenamento de artefatos entre runs; rastreabilidade via `model_version = {data}-{git_sha}-{tipo}` ligando `predictions` a `model_metrics` (`tipo` pode ser `ensemble-a-b`; o fallback recebe o sufixo `-fallback-naive` e grava as métricas do naive, com o campeão reprovado em `hyperparams`).
- **Localização:** `back-end/app/ml/` (não `ml_models/` na raiz, como docs antigas sugeriam) — reusa venv `uv`, seams de injeção dos repositories, camadas e suíte offline. Dependências no grupo `ml` do pyproject (torch CPU via índice dedicado), fora da imagem da API.
- **Validação:** split temporal por **data** (nunca por linha — símbolos correlacionados vazam informação cross-sectional) com embargo ≥ maior horizonte; walk-forward expanding-window com 4 folds contíguos sobre os últimos 180 dias (candidatos e gate avaliados no pool dos folds; skill por fold gravado para leitura de regime); backtest econômico long/flat com taxa+slippage, posição decidida no close de t capturando o retorno close_t→close_{t+1} (não há vela de abertura no dataset diário — o gap até a execução real é modelado pelo slippage).

## Consequências

- Prophet sai do vocabulário do projeto; README/ROADMAP atualizados no fechamento do marco.
- Dados externos (sentimento, on-chain, macro) — apontados pela revisão como o maior ganho — ficam explicitamente fora do v1 por exigirem pipelines novos de coleta; candidatos à iteração futura, junto com o timeframe 1h.
- DRL (trading autônomo) fora do escopo: não é forecasting e os resultados da literatura (114–341%) são simulados sem custos.
- Retreino diário implica previsões que podem variar entre dias mesmo sem dado novo relevante; aceito em troca de simplicidade operacional (sem storage de artefatos — por isso o scaler e os modelos não têm serialização). Se virar problema, a alternativa registrada é retreino semanal + artefato no Supabase Storage.
- Símbolos com histórico < `min_history_days` não entram no treino, mas recebem previsão (o modelo global generaliza); métricas reportadas por símbolo expõem onde a qualidade é pior.
