# ADR-0002 — Nuxt UI v4 (Tailwind v4) para componentes e TradingView Lightweight Charts v5 para o gráfico

Data: 2026-08-19 · Status: aceito

## Contexto

O dashboard precisa de forms com validação, select com busca, tabela ordenável, tabs, drawer/modal, toasts, skeletons e dark mode — e de um gráfico de candles com overlays (SMA/EMA/Bollinger), volume e painéis separados (RSI, MACD), com crosshair/zoom "de trading". A direção visual pode evoluir sem trocar essas bibliotecas; a especificação normativa atual vive em `docs/design/Design.md`.

## Decisão

- **Nuxt UI v4** como biblioteca de componentes (Reka UI + Tailwind v4). Tema e tokens são customizados conforme `docs/design/Design.md`. Cores de dados (alta/baixa, séries) vivem em `utils/constants.ts` + CSS vars `--cf-*`, nunca em `success`/`error` do tema.
- **Lightweight Charts v5** para o gráfico: `addSeries(CandlestickSeries|LineSeries|HistogramSeries|BaselineSeries, opts, paneIndex)`, panes com `setStretchFactor`, `WhitespaceData` para warm-up, formatadores pt-BR/UTC por série. Legenda, linha de corte e área reservada à previsão são HTML sobreposto posicionado com `timeToCoordinate`/`getHTMLElement`.

## Alternativas descartadas

- shadcn-vue / Tailwind puro: mais trabalho de forms/tabela/a11y para o mesmo resultado.
- ECharts: candlestick genérico, bundle maior, menos "trading feel"; não precisamos de gráficos genéricos no marco 1.

## Consequências

- Dependência da evolução do Nuxt UI (v4) e do Lightweight Charts (v5); ambos com skills instaladas para o agente (`nuxt-ui`, `lightweight-charts`).
- O gráfico é canvas: acessibilidade via `aria-label` descritivo + "Ver como tabela" (UTable com as últimas 50 velas).
- Logo de atribuição do TradingView mantido (licença Apache 2.0).
