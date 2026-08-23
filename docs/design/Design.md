# Design.md — Design System "Dark-Tech" (crypto-forecasting-app)

Versão 2 · 2026-08-22 · substitui a direção "Observatório" (v1, dark+light) como padrão do produto. Canvas de mockups (mesmo link, versão `v2-dark-tech`): https://claude.ai/code/artifact/d3e48655-f0d1-4113-b161-100ef74d5cd8

Decisões fechadas com o usuário (2026-08-22): **dark-only** · alta = **vela vazada em vidro branco-gelo** (baixa = vermelho) · telas de IA desenhadas no **estado final** com selo "IA · v0 · em validação" até o marco 3 entregar o modelo.

## 1. Conceito

Plataforma de **forecasting, analytics e inteligência com IA** — não uma exchange. Três marcas registradas:

1. **Vidro sobre navy**: cards translúcidos (glassmorphism) sobre fundo navy quase preto; a alta no gráfico é uma vela *de vidro* (vazada, contorno gelo), como na logo.
2. **Ciano = IA**: tudo que vem do modelo (previsões, gaps, resumos gerados, linha "esperada") usa o ciano do glow da logo — nunca outra coisa. O usuário aprende a cor uma vez.
3. **Snapshot, não live**: mantido da v1 — selo de snapshot + linha de corte; nada finge tempo real.

## 2. Cores (códigos HEX)

### 2.1 Fundos e superfícies

| Token | Valor | Uso |
|---|---|---|
| `--cf-bg` | `#060b16` | fundo da página (navy quase preto; nunca `#000`) |
| `--cf-bg-deep` | `#04070f` | painel esquerdo do login, texto sobre botão primário |
| `--cf-glass` | `linear-gradient(160deg, rgba(30,48,80,.42), rgba(12,22,42,.55))` + `backdrop-filter: blur(14px)` | cards de vidro |
| `--cf-solid` | `#0c1626` | superfícies que não podem ser translúcidas (canvas do gráfico, células sticky) |
| Luz ambiente | `radial-gradient(1200px 600px at 70% -10%, rgba(62,134,247,.10), transparent 60%)` | um único glow por página, no topo |

### 2.2 Bordas e texto

| Token | Valor | Uso |
|---|---|---|
| `--cf-border` | `rgba(216,230,245,.14)` | contorno padrão (branco-gelo 14 %) |
| `--cf-border-muted` | `rgba(216,230,245,.08)` | divisores internos |
| `--cf-border-strong` | `rgba(216,230,245,.26)` | card em destaque (glow) |
| `--cf-text-hi` | `#f6f9fd` | títulos, valores em destaque |
| `--cf-text` | `#dde6f2` | texto padrão |
| `--cf-text-muted` | `#9fb0c7` | rótulos, descrições (≥ 4.5:1 sobre bg) |
| `--cf-text-dim` | `#66788f` | placeholders, eixos |

### 2.3 Acentos

| Token | Valor | Regra de uso |
|---|---|---|
| `--cf-electric` | `#3e86f7` | **Azul elétrico** — ação primária, foco, nav ativa, links. Iluminação seletiva: no máximo ~20 % da composição; glow (`0 0 24px rgba(62,134,247,.35)`) só no botão primário e em **um** card de destaque por tela |
| `--cf-cyan` | `#5fc4ff` | **3ª cor (derivada do glow da logo)** — exclusiva de IA/previsão: chips "IA · v0", linha esperada, previsões na UI, ponto do selo de snapshot |
| `--cf-ice` | `#dbe7f5` | **Branco-gelo** — contornos, vela de alta (vazada), valores de alta |
| `--cf-down` | `#e5484d` | **Vermelho** — vela/indicador de baixa, erros |
| `--cf-warn` | `#d6b25e` | dourado — só para "dados velhos" (stale); sempre com ícone + texto |

**Proibido**: roxo, rosa, verde, laranja e gradientes multicoloridos. Os únicos gradientes permitidos são os monocromáticos do vidro e a luz ambiente azul.

### 2.4 Séries do gráfico

Família azul/gelo com **estilo de traço + espessura** como codificação secundária obrigatória (a restrição de matiz do brief impede distinguir séries só por cor — resultado do validador `dataviz` registrado em [audit.md](audit.md)):

| Série | Cor | Traço |
|---|---|---|
| Vela alta | `#dbe7f5` corpo `rgba(219,231,245,.10)` | **vazada**, contorno 1 px (opção "preenchida" em Preferências → Acessibilidade) |
| Vela baixa | `#e5484d` | preenchida |
| SMA 20 / 50 / 200 | `#4f8ff7` / `#2596be` / `#c8d9ef` | contínua 1.2 / 1.8 / 2.2 px |
| EMA 12 / 26 | `#8ab8ff` / `#2f5fd0` | tracejada 1.2 / 1.8 px |
| Bollinger | `rgba(200,217,239,.55)`, banda 5 % | pontilhada |
| Volume | alta `rgba(219,231,245,.28)` / baixa `rgba(229,72,77,.30)` | histograma |
| RSI | `#4f8ff7` | contínua; faixas 30/70 |
| MACD linha / sinal | `#4f8ff7` / `#dbe7f5` | histograma ±: gelo/vermelho a 45 % |
| **Cenário melhor / esperado / pior** | `#dbe7f5` / `#5fc4ff` / `#e5484d` | tracejadas após a linha de corte; faixa ciano 8 %; rótulos na ponta direita |

Legenda com valores é obrigatória (canal de alívio para as séries de baixo contraste).

## 3. Tipografia — Google Sans

| Papel | Fonte | Escala |
|---|---|---|
| UI e títulos | **Google Sans** (fallback `'Segoe UI', system-ui, sans-serif`) | corpo 13.5/1.5 · h1 24/700 (páginas) e 31/700 (login) · seção 15/700 · tracking −0.01em em títulos |
| Números, horários, símbolos | **Google Sans Code** (fallback `ui-monospace, Consolas`) | `font-variant-numeric: tabular-nums` em todo número; preço destaque 24/500 |
| Eyebrow | Google Sans Code 11/500, caixa alta, +0.08em | "BEM-VINDO NOVAMENTE, GABRIEL", cabeçalhos de tabela, selo |

Carregamento: ambas servidas pelo Google Fonts CDN (verificado 2026-08-22: `css2?family=Google+Sans` responde 200). No build estático, preferir **self-host** com `font-display: swap` (o proxy pode mudar; baixar os woff2 no build).

## 4. Layout e regras para desenvolvedores

- **Raio**: 12 px cards de vidro, 8 px controles/inputs, 999 px chips. Nada além desses três.
- **Grade**: 4 px; gaps usuais 8/12/16; padding de página 24 px; header 58 px.
- **Vidro**: `background: var(--cf-glass); border: 1px solid var(--cf-border); border-radius: 12px; box-shadow: inset 0 1px 0 rgba(255,255,255,.07); backdrop-filter: blur(14px)`. Fallback `@supports not (backdrop-filter: blur(1px))` e `prefers-reduced-transparency`: fundo sólido `#0d1729`.
- **Card destacado** (`glass-hi`): borda 26 % + glow elétrico — **no máximo um por tela** (usado no "Leitura do dia" e "Resumo da rodada").
- **Botões**: primário = elétrico com texto `#04070f` (contraste 7.4:1) e glow; secundário = vidro com borda; ghost sem borda. Altura 34 (toolbar) / 40 (formulários); alvo ≥ 44 px no mobile.
- **Foco**: `outline: 2px solid var(--cf-electric); outline-offset: 2px` em tudo que é interativo.
- **Logo**: `front-end/public/crypto-forecasting-logo-v5.png`; sobre o navy usar `mix-blend-mode: screen` (o fundo preto da imagem some). Header 28 px, login 170 px, favicon derivado.
- **Nada de**: sombras pretas puras, `#000`/`#fff` puros, emoji como ícone, mais de um glow por tela, "LIVE"/"tempo real" na UI.
- Ícones: Lucide (stroke 2), 16 px na UI, 20–24 px em estados; GitHub/LinkedIn no rodapé do login.

## 5. Telas (wireframes entregues no canvas)

| Tela | Rota | Estrutura |
|---|---|---|
| **Login** (split, ref. IAagro) | `/login` | Esq. (55 %): marca no topo, logo grande, headline "Enxergue o mercado um dia à frente.", 3 bullets do conceito, rodapé "Projeto desenvolvido por Gabriel Castro" + ícones GitHub/LinkedIn (links). Dir.: card de vidro com o formulário. Variantes: erro genérico, sessão expirada. Demais telas de auth (cadastro, confirme e-mail, esqueci, redefinir) em card central de vidro — mensagens da [ux-spec.md](ux-spec.md) §3 inalteradas |
| **Início** (nova) | `/` | Eyebrow ciano "Bem-vindo novamente, {nome}" + "As principais mudanças no mercado desde o seu último acesso" (timestamp do último login vem do Supabase Auth). 3 InsightCards top-5: volatilidade (ATR 14 relativo), **gap real × projeção** (IA), volume 24h vs média 7d. Abaixo: "Leitura do dia" (resumo textual gerado, glass-hi) e 2 atalhos (Continuar de onde parou · Configurar alertas). Clique em linha → `/graficos?symbol=X` |
| **Gráficos** | `/graficos` | O dashboard de candles da v1 re-skinado + **cenários do modelo**: depois da linha de corte, 3 linhas tracejadas (melhor gelo / esperada ciano / pior vermelho) com faixa ciano — toggle no grupo "Modelo" do painel de indicadores. Stat strip ganha o tile "Previsão diária (IA)" em ciano |
| **Previsões** | `/previsoes` | Chips do modelo (versão, MAE, acerto de direção) · **Resumo da rodada em texto** (gerado por agente; cita variação % dos top 3 gaps, média por horizonte e disclaimer "cenários, não recomendação") · tabela top-20: Ativo · Preço real · Previsão diária · Semanal · Mensal · Anual (valor + % vs real; gelo acima / vermelho abaixo) · Confiança (%) · cards: **Monte Carlo com backtesting (Em breve)** e atalho para os cenários no gráfico |
| **Mercado** | `/mercado` | Tabela 24h da v1 re-skinada (mesmas colunas/regras) |
| **Preferências** (nova) | `/preferencias` | Dados pessoais (nome, e-mail, telefone com máscara BR) · Acessibilidade ("Velas de alta preenchidas") · Notificações: toggle geral + tópicos (gaps, volume, volatilidade, novas rodadas) + canal E-mail ativo, SMS/WhatsApp "(Em breve)". Telefone: `type="tel"`, `autocomplete="tel"`, guardado no perfil (tabela `profiles` futura, RLS por usuário) |
| Nav | — | `Início · Gráficos · Previsões · Mercado` (desktop e barra inferior mobile); conta → Preferências, Sair. Sem toggle de tema |

Métricas analíticas extras sugeridas (para afastar de exchange, já refletidas nos mockups): confiança por horizonte, MAE/acerto de direção da rodada, gap real×projeção como métrica de 1ª classe, ATR relativo como volatilidade, volume vs média 7d (não volume bruto).

## 6. Estados, dados de IA e honestidade

- Todos os estados da v1 valem sem mudança ([ux-spec.md](ux-spec.md) §7): loading/vazio/erro/warm-up/stale/sessão — re-skinados no artboard "Estados".
- Enquanto `/forecasts` não existir (marco 3): os blocos de IA mostram o **estado final** com chip `IA · v0 · em validação`; se a API não devolver previsões, o bloco inteiro vira EmptyState "O modelo ainda não publicou previsões para este ativo." — nunca números inventados.
- Disclaimer fixo em qualquer superfície de previsão: "Leia as previsões como cenários, não como recomendação de compra ou venda."
- "Desde o seu último acesso": guardar `last_seen_at` no perfil; se for o primeiro acesso, título vira "O mercado nas últimas 24 h".

## 7. Rastreabilidade

- Mockups: gerados por [canvas/build.mjs](canvas/build.mjs) (v2; a v1 "Observatório" está em [canvas/v1/](canvas/v1/)). Capturas em [mockups/](mockups/).
- Paleta: restrições de matiz do brief tornam impossível passar o gate completo do validador `dataviz` para 5 overlays simultâneos — mitigação documentada (traço/espessura/legenda) em [audit.md](audit.md); velas gelo×vermelho passam CVD com folga (ΔE deutan 30.3).
- Base de UX (fluxos de auth, microcopy, frescor, a11y): [ux-spec.md](ux-spec.md) continua válida; onde este arquivo divergir (cores, nav, telas novas), **este arquivo vence**.
