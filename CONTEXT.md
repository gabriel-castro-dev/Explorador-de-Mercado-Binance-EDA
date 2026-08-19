# CONTEXT.md — glossário do domínio

Vocabulário único do projeto (back-end, API, front-end e docs). Use estes termos; evite os sinônimos indicados. Decisões de arquitetura ficam em `docs/adr/`.

| Termo | Definição | Evitar |
|---|---|---|
| **Ativo** / **símbolo** | Par negociado na Binance, ex.: `BTCUSDT` (sempre caixa alta, `translate="no"` na UI). O **universo** é o top 20 pares USDT por volume 24h e **drifta**: a tabela `symbols` acumula ativos históricos, então um ativo pode existir sem dados recentes. | "moeda", "ticker" (reservado ao snapshot 24h) |
| **Timeframe** | Granularidade das velas: `15m`, `1h`, `1d`. `24h` é apenas um sinônimo legado de `1d` aceito pela API (tabela `features_24h`); o front usa só os três canônicos. | "intervalo", "período" |
| **Kline** / **vela** / **candle** | Linha OHLCV de `klines_{tf}` (`open_time`, `open`, `high`, `low`, `close`, `volume`…). A API devolve **newest-first**, sem paginação (`limit` ≤ 1000). | "barra", "preço" (genérico) |
| **Feature** / **indicador** | Linha calculada de `features_{tf}` keyed por `timestamp`: SMA 20/50/200, EMA 12/26, RSI 14, MACD (linha, sinal, histograma), Bollinger (sup/méd/inf, largura), ATR 14, desvios vs SMA, variação % de preço, variação de volume 24h, SMA de volume, spread bid-ask, desequilíbrio do book. É a entrada dos modelos de ML. | "métrica", "sinal" |
| **Warm-up** | Janela inicial em que um indicador é `null` porque ainda não há velas suficientes para a janela de cálculo (ex.: SMA 200 só a partir da 200ª vela). É **normal**, não erro: no gráfico vira gap (`WhitespaceData`), na legenda `—` + "warm-up até <data>" ou "faltam N velas". | "dado faltante", "bug" |
| **Snapshot 24h** / **resumo 24h** | Linha mais recente de `ticker_24hr_history` por ativo (`/tickers/24h`): último preço, variação, abertura/máx/mín, preço médio ponderado, bid/ask, volumes, nº de trades. Atualiza **de hora em hora**. | "ticker" isolado, "cotação ao vivo" |
| **Snapshot** (selo) | Declaração de frescor na UI: "Velas: 19 ago 00:00 UTC · há 6 h". Candles e indicadores atualizam **1×/dia (~00:05 UTC)**; nada é tempo real. | "live", "ao vivo", "tempo real" (proibidos na UI) |
| **Stale** / **dados velhos** | Estado do selo quando a última vela passa de 26 h (15m/1h) ou 50 h (1d), ou o snapshot 24h passa de 2 h. Mostra aviso; nunca bloqueia o gráfico. | "offline", "erro" |
| **Linha de corte** | Linha vertical tracejada após a última vela observada; à direita fica a área reservada à **previsão** (marco ML). | "agora", "presente" |
| **Previsão** / **forecast** | Saída futura dos modelos (`/api/v1/forecasts`, tabelas `predictions`/`model_metrics`) — ainda não existe; a UI reserva a aba "Previsões (em breve)" e o slot no gráfico. | "predição", "projeção" |
| **Publishable key** vs **service_role** | A publishable key (`sb_publishable_…`, antes "anon key") é a única que pode chegar ao navegador e à API; a service_role só existe nos jobs. | "anon key" (legado), "api key" (ambíguo) |
| **Sessão** | Sessão do Supabase Auth gerida pelo supabase-js no navegador (fluxo implícito, localStorage). A API só valida o access token (JWKS) e aplica RLS. | "token manual", "cookie de auth" |
| **Retenção** | Política de limpeza por tabela: `klines_15m` 7 dias, `klines_1h` 30 dias, `klines_1d` permanente; `features_15m` 180 d, `features_1h` 2 anos, `features_24h` permanente; `ticker_24hr_history` 30 d; `orderbook_tickers` 7 d. | — |
