# Inventário de componentes — mapeado para Nuxt UI v4

Princípios (de `composition-patterns`, adaptados a Vue): **sem proliferação de props booleanas** (estados vêm de um objeto `status: 'idle'|'loading'|'empty'|'error'|'ready'` ou de variantes explícitas, não de `isLoading`/`isEmpty`/`hasError`); **estado levantado para composables** (`useDashboardQuery`, `useIndicatorPrefs`) e injetado, nunca duplicado em props-drilling; **slots em vez de render-props**; componentes de bloco (`ChartPanel`, `Tickers24hTable`) são *compound* — header/corpo/rodapé via slots com contexto compartilhado por `provide/inject`.

Tema (`app.config.ts`): `ui.colors = { primary: 'indigo', neutral: 'zinc' }`; `@theme { --font-sans: "IBM Plex Sans"; --font-mono: "IBM Plex Mono"; --ui-radius: 6px }`. Cores de dados (alta/baixa/séries) **não** passam pelo tema do Nuxt UI: vivem em `utils/constants.ts` (`INDICATOR_DEFS`, `CANDLE_COLORS`) e em CSS vars `--cf-*` (ver [tokens.md](tokens.md)).

| Componente (arquivo) | Nuxt UI base | Props / variantes relevantes | Estados | A11y |
|---|---|---|---|---|
| **AppHeader** (`layouts/default.vue`) | `UHeader` + `UNavigationMenu` (horizontal) + `UDropdownMenu` (conta) + `UButton` (tema, `useColorMode`) | items: Dashboard, Mercado, Previsões (`disabled: true`, `badge: 'EM BREVE'`) | — | `aria-label="Principal"`; item desabilitado anuncia "em breve" |
| **MobileTabBar** | `UNavigationMenu` orientation horizontal, fixo no rodapé (`md:hidden`) | 3 itens contextuais (Dashboard / Mercado / Indicadores ou Previsões) | ativo via rota | alvos 48 px; `aria-current="page"` |
| **SymbolSelector** | `USelectMenu` (`searchable`, `:items`, `value-key="symbol"`, `:loading`) | `v-model` ↔ `useDashboardQuery().symbol`; slot `#item` (símbolo mono + nome + último/var%), slot `#empty` "Nenhum ativo encontrado", slot `#content-bottom` rodapé de contagem | loading (botão skeleton, `disabled`), error (ícone alerta + tooltip + retry no menu) | combobox nativo do Reka (↑↓ Enter Esc); `aria-label="Ativo"` |
| **TimeframeToggle** | `UTabs` (`variant="pill"`, `size="sm"`, `:content="false"`) **ou** `URadioGroup` (`variant="card"`, horizontal) — preferir `UTabs` pela estética segmentada | `items: [{label:'15m',value:'15m'},…]`; `v-model` ↔ `tf` | — | setas ←→; rótulo do grupo "Timeframe"; subtítulo em `UBadge variant="subtle"` |
| **DataFreshnessBadge** | `UBadge` (`variant="subtle"`, `color="neutral"|"warning"`, `size="lg"`) dentro de `UTooltip` | `source: 'klines'|'tickers'`; `lastAt: Date`; calcula `isStale` (26 h / 2 h) | fresh · stale · loading (`USkeleton` interno) · error ("—") | `tabindex="0"` para tooltip por foco; `aria-live="polite"` ao mudar de estado |
| **RefreshButton** | `UButton` (`icon="i-lucide-refresh-cw"`, `:loading`, `color="neutral"`, `variant="outline"`) | `@click="refreshAll"` | loading: spinner, label "Atualizando…" | `aria-label` quando só ícone (mobile) |
| **ChartPanel** (compound) | `UCard` (`:ui="{ body: 'p-0' }"`) | slots `#legend`, `#default` (canvas), `#footer`; `status` | loading → `ChartSkeleton`; empty → `EmptyState`; error → `ErrorState`; ready | container com `aria-label` descritivo + botão "Ver como tabela" (abre `UModal` com `UTable`) |
| **CandlestickChart.client** | Lightweight Charts v5 (sem Nuxt UI) | `candles`, `volume`, `overlays: Record<key, LineData|Whitespace>`, `panes`, `theme` (light/dark via `applyOptions`), `cutLineTime` | warm-up = `WhitespaceData` (gap natural) | `touch-action:none` no canvas; respeita `prefers-reduced-motion` (sem animação de série) |
| **ChartLegend** | próprio (div absoluta) + `UBadge` para notas | `rows: {key,label,color,style,value|null,warmupNote}`; valores do crosshair via `subscribeCrosshairMove` | sem crosshair = última vela | texto em tokens de texto (nunca na cor da série); swatch decorativo `aria-hidden` |
| **CutLineMarker** | série de `createSeriesMarkers`/`PriceLine`… → na prática: linha vertical via `timeScale` + overlay HTML posicionado | `time`, `label` | — | descrito no `aria-label` do gráfico ("dados até 19 ago 00:00 UTC") |
| **IndicatorToggles** | `UCheckboxGroup` (desktop; `variant="list"`, items com slot `#label` para swatch) agrupado por `<fieldset>`; mobile: `UDrawer` + `USwitch` por item | `v-model` ↔ `useIndicatorPrefs()`; `INDICATOR_DEFS` (key, label, color, lineStyle, pane); ações `UButton variant="ghost"` Restaurar/Limpar | item com nota `warm-up` (UBadge) quando a série não tem janela | `fieldset/legend` por grupo; `aria-label="Indicadores"` no `aside`; Espaço alterna |
| **Stat tile / KpiStrip** | `UCard` container + grid (`grid-cols-2 md:grid-cols-7`) de tiles próprios | `items: {label, value|null, sub?, tone?: 'up'|'down'}` | skeleton por tile; null → "—" | rótulo visível; valor em `tabular-nums`; tom sempre com ▲/▼ |
| **Tickers24hTable** | `UTable` (`:data`, `:columns` TanStack, `v-model:sorting`, `sticky`, `:loading`, `@select`) | colunas com `meta.class.td = 'text-right font-mono tabular-nums'`; célula Var. % via slot `#price_change_percent-cell`; `row.class` selecionada | loading (`loading-animation="carousel"` + skeleton rows), empty (`#empty` → EmptyState), error (ErrorState externo) | linhas focáveis (`tr tabindex=0`, `@keydown.enter`); `aria-sort` gerado pelo UTable; filtro `UInput type="search"` |
| **MarketListMobile** | `UCard` + `<a>` rows (`NuxtLink`) + `UDropdownMenu` para ordenação | `rows`, `sortKey` | idem tabela | alvos 56 px; link real (não div) |
| **EmptyState / ErrorState** | próprios: `UIcon` (lucide 24) + título + texto + `UButton`s | `title`, `description`, `actions[]`, `detail?` (mono, ex. `GET /klines/1h · 503`) | — | `role="status"` (empty) / `role="alert"` (error); botão primário recebe foco ao aparecer |
| **ChartSkeleton** | `USkeleton` com a geometria dos panes | `panes: number` | — | `aria-busy="true"` no container; texto "Carregando BTCUSDT · 1h…" |
| **OnboardingHint** | `UPopover` (não modal, ancorado ao painel) ou `UCard` absoluto | `open` (localStorage `cf:onboarded:v1`) | — | `role="dialog"` não modal; Esc fecha; foco não é roubado |
| **AuthLayout / AuthCard** | `layouts/auth.vue` + `UCard` (max-w 400) | slot header (logo), default, footer | — | `h1` por tela; `lang="pt-BR"` |
| **AuthForm** | `UForm` (`:schema` zod/valibot, `:state`) + `UFormField` + `UInput` + `UButton` (`:loading`, `block`) | mensagens de validação inline; `UAlert color="error"` no topo para erro genérico | idle · submitting · error · success (`role="status"`) | erros ligados ao campo por `aria-describedby` (UFormField faz) |
| **PasswordField** | `UInput type="password"` + `UButton` trailing (`variant="link"`, `aria-label="Mostrar senha"`) + `UProgress`/barra própria de força com rótulo textual | `v-model`, `showStrength` | — | `aria-pressed` no olho; `autocomplete="current-password"|"new-password"` |
| **SessionExpiredBanner** | `UAlert` (`color="neutral"`, `variant="subtle"`, `icon="i-lucide-clock"`) | lê `?reason=expired` | — | `role="status"` |
| **Toasts** | `useToast()` (`UApp` já provê `UToaster`) | sucesso/neutro; nunca para info que exige ação | — | `aria-live` do Toaster |
| **ThemeToggle** | `UButton` ghost + `useColorMode()` | alterna light/dark; persiste | — | `aria-label="Alternar tema claro/escuro"` |
| **AccountMenu** | `UDropdownMenu` (items: e-mail (disabled), Preferências → `UModal` com `USwitch` "Velas de alta vazadas", Sair) | — | — | — |
| **(futuro) ForecastOverlay / ModelMetricsCard** | série `AreaSeries`/`BaselineSeries` + `UCard` com 4 tiles | reservado (marco 3) | — | — |

## Regras transversais

- Todo número: classe `font-mono tabular-nums` (`text-right` em tabela).
- Nenhum componente recebe `isLoading`+`isEmpty`+`hasError`: recebe `status` (ou `AsyncData` de `useAsyncData`) e decide a variante; estados são componentes explícitos (`EmptyState`, `ErrorState`, `ChartSkeleton`).
- Cores de série só por `INDICATOR_DEFS[key].color[mode]` — nunca hardcoded em template.
- Semântica Nuxt UI: `success`/`error` reservados a feedback de sistema (toast, validação); alta/baixa usam `--cf-up`/`--cf-down`.
- Ícones `i-lucide-*` 16 px (toolbar) / 20–24 px (estados). Sem emoji.
