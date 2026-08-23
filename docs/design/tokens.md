# Tokens de design — dashboard crypto-forecasting-app

Direção: **"Observatório"** — ferramenta analítica sóbria que observa *snapshots* diários, não um terminal ao vivo.
Realizável com Nuxt UI v4 (`app.config.ts` → `ui.colors`) + Tailwind v4 (`@theme`) + Lightweight Charts v5 (`applyOptions`).

## 1. Cor — chrome da aplicação

Mapeamento Nuxt UI: `primary: 'indigo'`, `neutral: 'zinc'`, `success`/`error` **não** são usados para alta/baixa (essas cores são tokens de dados, abaixo).

| Token (CSS var) | Light | Dark | Uso / classe Nuxt UI |
|---|---|---|---|
| `--ui-bg` | `#fafafa` | `#18181b` | fundo da página (`bg-default`) |
| `--ui-bg-elevated` | `#ffffff` | `#1f1f23` | cards, painel de toggles, header (`bg-elevated`) |
| `--ui-bg-muted` | `#f4f4f5` | `#26262b` | hover de linha, zebra (`bg-muted`) |
| `--ui-bg-accented` | `#e4e4e7` | `#2e2e34` | item selecionado (`bg-accented`) |
| `--ui-border` | `#e4e4e7` | `#2e2e34` | bordas padrão (`border-default`) |
| `--ui-border-muted` | `#ededf0` | `#26262b` | divisores finos, grade do gráfico |
| `--ui-text-highlighted` | `#18181b` | `#fafafa` | títulos, preços em destaque |
| `--ui-text` | `#27272a` | `#e4e4e7` | texto padrão |
| `--ui-text-muted` | `#52525b` | `#a1a1aa` | rótulos, legendas (AA ≥ 4.5:1 sobre bg) |
| `--ui-text-dimmed` | `#8b8b94` | `#71717a` | placeholders, eixos do gráfico |
| `--ui-primary` | `#4f46e5` (indigo-600) | `#818cf8` (indigo-400) | ação primária, foco, link, RSI |
| `--ui-primary-soft` | `#eef2ff` | `rgba(129,140,248,.14)` | fundo de chip/toggle ativo |
| `--cf-warning` | `#b45309` / fundo `#fffbeb` | `#fbbf24` / fundo `rgba(251,191,36,.12)` | badge de frescor "dados velhos" (sempre com ícone + texto) |
| `--cf-danger` | `#b91c1c` / fundo `#fef2f2` | `#f87171` / fundo `rgba(248,113,113,.12)` | erro de API, validação |

Anel de foco: `outline: 2px solid var(--ui-primary); outline-offset: 2px` (visível em todos os controles, inclusive linhas de tabela e toggles).

## 2. Cor — dados (gráfico e tabela)

Validado com `dataviz/scripts/validate_palette.js` (OKLab, CVD Machado 2009) em 2026-08-19.

### Velas / variação (par divergente alta ↔ baixa)

| Papel | Light | Dark | Resultado do validador |
|---|---|---|---|
| Alta (`up`) | `#0f9d58` | `#26a69a` | dark: PASS completo (ΔE deutan 11.6) |
| Baixa (`down`) | `#d93025` | `#ef5350` | light: WARN deutan ΔE 6.1 (faixa 6–8) → **codificação secundária obrigatória** |
| Neutro (sem variação / null) | `#8b8b94` | `#71717a` | |

Codificação secundária (sempre presente, não opcional): setas `▲`/`▼` e sinal `+`/`−` junto a toda variação %; opção de acessibilidade **"Velas de alta vazadas"** (corpo da alta transparente com borda, baixa preenchida) em Conta → Preferências; no histograma MACD, barras positivas acima e negativas abaixo da linha zero (posição já codifica sinal).

### Overlays do pane de preço (categórico, ordem fixa — nunca reciclar)

Ordem/slots seguem o tema padrão da skill `dataviz`; light passa todos os checks adjacentes (pior ΔE CVD 16.3); dark idem (13.2). Além da cor, cada família tem **estilo de traço** (codificação secundária): SMA contínua, EMA tracejada, Bollinger pontilhada + banda; período mais longo = traço mais grosso.

| Slot | Série | Light | Dark | Traço |
|---|---|---|---|---|
| 1 | SMA 20 | `#2a78d6` | `#3987e5` | contínuo 1 px |
| 2 | SMA 50 | `#eb6834` | `#d95926` | contínuo 1.5 px |
| 3 | SMA 200 | `#4a3aa7` | `#9085e9` | contínuo 2 px |
| 4 | EMA 12 | `#eda100` | `#c98500` | tracejado 1 px (light: contraste 2.07:1 → valor sempre visível na legenda) |
| 5 | EMA 26 | `#e87ba4` | `#d55181` | tracejado 1.5 px (light: 2.58:1 → idem) |
| — | Bollinger (sup/méd/inf) | `#6b7280` linhas, banda `rgba(107,114,128,.08)` | `#9ca3af`, banda `rgba(156,163,175,.10)` | pontilhado 1 px; média tracejada |
| — | Volume | alta `rgba(15,157,88,.35)` / baixa `rgba(217,48,37,.35)` | `rgba(38,166,154,.35)` / `rgba(239,83,80,.35)` | histograma, escala própria (20 % inferior do pane) |

Colisão conhecida: baixa (`#d93025`) × SMA 50 (`#eb6834`) ΔE normal 10.5 — mitigada por **tipo de marca** (corpo preenchido × linha fina) e legenda com valores; não usar laranja para nada além da SMA 50.

### Panes de osciladores

| Série | Light | Dark | Nota |
|---|---|---|---|
| RSI 14 | `#4f46e5` | `#818cf8` | série única do pane (usa o primário); faixas 30/70 em `--ui-border` tracejado, zona 30–70 sombreada 4 % |
| MACD linha | `#2a78d6` | `#3987e5` | slot 1 (mesma cor da SMA 20, pane diferente, legenda própria) |
| MACD sinal | `#eb6834` | `#d95926` | slot 2 |
| MACD histograma | alta/baixa a 60 % de opacidade | idem | divergente em torno de zero |

### Futuro — previsões (reservado)

Faixa projetada: preenchimento `--ui-primary` a 10–14 % + linha mediana tracejada `--ui-primary`; marcador "linha de corte" no último candle observado (ver spec). Nenhuma cor nova.

## 3. Tipografia

| Papel | Fonte | Tamanho / peso / altura | Observação |
|---|---|---|---|
| UI (texto, botões, labels) | **IBM Plex Sans** (fallback `system-ui`) | 13 / 400 / 1.45 base; 14 em formulários | `font-feature-settings: "ss01"` opcional |
| Títulos | IBM Plex Sans 600 | 20 / 1.2 (página), 15 / 1.3 (seção) | tracking −0.01em |
| Números e dados | **IBM Plex Mono** (fallback `ui-monospace`) | 13 / 400; preço destaque 22 / 500 | `font-variant-numeric: tabular-nums`; todo preço, %, horário UTC e eixo do gráfico |
| Microcopy / eyebrow | IBM Plex Mono 11 / 500, caixa alta, tracking +0.06em | selo de frescor, cabeçalho de tabela | |

Escala (px): 11 · 12 · 13 · 14 · 16 · 20 · 24. Nuxt UI: `--font-sans: "IBM Plex Sans"`, `--font-mono: "IBM Plex Mono"` em `@theme`.

## 4. Espaço, raio, elevação

- Grade de 4 px; espaçamentos usuais 8 / 12 / 16 / 24 / 32.
- Raio: `--ui-radius: 6px` (controles), 8 px cards, 999 px chips/badges. Nada acima de 8 px (tom instrumental).
- Elevação: **sem sombra** em light (borda 1 px `--ui-border`); em dark, superfície mais clara que o fundo + borda. Dropdowns/popovers: sombra `0 8px 24px rgba(0,0,0,.10)` (light) / `.45` (dark).
- Controles: altura 32 px (toolbar), 36 px (formulários de auth), alvo de toque ≥ 44 px no mobile.
- Gráfico: grade `--ui-border-muted` horizontal apenas; eixos em `--ui-text-dimmed` mono 11 px; crosshair `--ui-text-dimmed` tracejado; fundo do gráfico = `--ui-bg-elevated`.

## 5. Ícones

Lucide (`i-lucide-*`, padrão do Nuxt UI), 16 px na toolbar, 20 px em estados vazios/erro. Nunca emoji.
