# Auditoria — Web Interface Guidelines (vercel-labs) sobre os mockups

Data: 2026-08-19 · Fonte das regras: `web-interface-guidelines/command.md` (buscado no dia) · Alvo: os 23 artboards gerados por `docs/design/canvas/build.mjs` (a mesma fonte do canvas publicado).

Como os artboards são mockups estáticos, parte dos achados é "não aplicável no mockup, obrigatório na implementação" — esses viraram regras na [ux-spec.md](ux-spec.md) (§9) e em [components.md](components.md). Abaixo, o que foi **ajustado nos mockups** e o que foi **transferido para a spec**.

## Ajustado nos mockups (republicado no canvas, versão "auditoria-aplicada")

| Regra | Achado | Ajuste |
|---|---|---|
| `<a>` para navegação, `<button>` para ação | barra inferior mobile usava `<button>` para Dashboard/Mercado/Previsões | itens de navegação viraram `<a aria-current>`; "Indicadores" (abre drawer) continua `<button aria-haspopup="dialog">`; "Previsões" recebe `aria-disabled` |
| Headings hierárquicos | Dashboard não tinha `h1` (só título visual na toolbar) | `h1` visualmente oculto "Dashboard" (sr-only) |
| `text-wrap: balance` em títulos | ausente | aplicado a todos os `h1` |
| Aspas curvas | texto do estado "Sessão expirada" usava `"..."` retas | trocado por “ ” |
| `translate="no"` em identificadores | símbolo `BTCUSDT` traduzível | `translate="no"` no símbolo do seletor (regra estendida a todo símbolo na spec) |
| Safe areas | barra inferior mobile sem `env(safe-area-inset-bottom)` | `padding-bottom: max(8px, env(safe-area-inset-bottom))` |
| Loading termina com `…` | ok ("Carregando BTCUSDT · 1h…", "Atualizando…", "Confirmando…") | — |
| Botões só-ícone com `aria-label` | ok (tema, conta, atualizar mobile, fechar, mostrar senha) | — |
| Ícones decorativos `aria-hidden` | ok (todos os SVGs inline) | — |
| Números tabulares | ok (`.mono { tabular-nums }` em toda célula/valor) | — |
| Estado vazio tratado | ok (seletor, gráfico, tabela, tile) | — |
| Hover em links | ok (`a:hover` definido) | — |

## Transferido para a spec / implementação (não verificável em mockup estático)

| Regra | Onde ficou |
|---|---|
| Foco visível `:focus-visible`, nunca `outline-none` sem substituto; sticky bars não cobrem foco (`scroll-padding-bottom` = altura da barra) | ux-spec §9; tokens §1 (anel) |
| Inputs com `autocomplete` (`email`, `current-password`, `new-password`), `type="email"`, `inputmode`, `spellcheck="false"` no e-mail; nunca bloquear paste; label clicável; erro inline + foco no primeiro erro; botão habilitado até o request começar | ux-spec §3; components (AuthForm, PasswordField) |
| Checkbox + label num único alvo (toggle de indicador) | components (IndicatorToggles: `<label>` envolve o controle) |
| `prefers-reduced-motion` (shimmer do skeleton, transições) | ux-spec §9 |
| `Intl.DateTimeFormat`/`Intl.NumberFormat` (pt-BR, UTC) em vez de formatos fixos | ux-spec §9 + plano (`utils/time.ts`) |
| URL reflete estado (`?symbol&tf`), deep-link, links com Cmd/Ctrl+clique na tabela (linhas navegam via `<a>`/`NuxtLink` no mobile; no desktop `@select` + link real na célula Ativo) | ux-spec §2, §5 |
| `touch-action: manipulation` global; `touch-action: none` só no canvas do gráfico; `overscroll-behavior: contain` no drawer/modal; gestos (pinch/drag) têm alternativa por teclado (± zoom, ←→ pan) e botões | ux-spec §8–9 |
| `color-scheme: dark` no `<html>` e `<meta name="theme-color">` por tema | components (ThemeToggle) — adicionar em `nuxt.config` `app.head` |
| `aria-live="polite"` em toasts, selo de frescor, resultado de validação | ux-spec §6, §9 |
| Texto longo: `min-w-0` + `truncate` nos tiles e no e-mail do header (já truncado no mockup "gabriel@…") | components (KpiStrip, AccountMenu) |
| Listas > 50 itens virtualizadas — **não se aplica** (20 ativos; tabela alternativa do gráfico limita a 50 velas) | — |
| Ações destrutivas com confirmação — único caso: "Limpar tudo" nos toggles → usar toast com **Desfazer** (5 s) em vez de modal | ux-spec §4.3 (adicionado) |
| `<img>` com dimensões / lazy — não há imagens | — |
| Fontes: `<link rel="preconnect">` para fonts.googleapis/gstatic ou self-host Plex com `font-display: swap` (recomendado self-host no build estático) | components (tema) |

## Resultado

Nenhum achado aberto nos mockups após os ajustes. Itens de implementação listados acima devem entrar no checklist do marco 2 (UX & Usabilidade) do `docs/ROADMAP.md`.

## Segunda passada (revisão independente dos artboards, mesmo dia)

Ajustes aplicados após uma revisão de consistência sobre os 23 artboards (canvas republicado, versão "segunda-passada"):

- Números: RSI com vírgula decimal (`53,1`), MACD com sinal de menos tipográfico (`−445`), tile Máx/Mín com decimais (`114.120,0 · 110.902,1`), "há 12 min" em vez de "há 0h12"; volume base do BCHUSDT corrigido.
- `—` deixou de ser ambíguo: agora significa **só** "campo nulo/sem dados"; "sem variação" é `+0,00 %` em cinza **sem seta** (tabela, lista mobile, menu do seletor). Legenda do rodapé da tabela atualizada; spec §5 idem.
- Cartão "Warm-up parcial" corrigido para `1h` (tinha `1d` com eixo horário); rodapé do gráfico diz `exibindo 92 de 720 velas`.
- Marca unificada como "crypto forecasting" também no mobile; amostra de data nos tokens no formato da UI.
- Copy do erro do gráfico: removido "Seus dados não foram perdidos" (não há dado do usuário num gráfico somente leitura).
- A11y nos mockups: "mostrar senha" virou `<button aria-pressed>`; `aria-current="page"` na nav desktop; `for`/`id` nos campos de auth; `tabindex` em cabeçalhos ordenáveis e nos controles com `role=checkbox|switch`.
- Artboard Tokens: altura do frame 980 px (conteúdo não é mais cortado).

Não alterado (de propósito): só o login tem variante dark entre as telas de auth — as demais seguem os mesmos tokens e não ganhariam informação nova.

## v2 Dark-Tech (2026-08-22) — validação de paleta e desvios documentados

O redesign Dark-Tech proíbe verde, roxo, rosa e laranja — as matizes que faziam a paleta v1 passar o gate completo do validador `dataviz`. Resultados sobre a superfície `#0c1626`:

- **Velas gelo (`#dbe7f5`) × vermelho (`#e5484d`)**: CVD deutan ΔE 30.3, visão normal 36.4, contraste ≥ 3:1 — todos PASS. O gelo fica acima da banda de luminosidade dark do validador por decisão de design (a vela de alta é *vazada*: a forma, não o preenchimento, carrega a identidade). Reforço: opção "Velas de alta preenchidas" em Preferências.
- **Overlays (família azul/gelo `#4f8ff7 #2596be #c8d9ef #8ab8ff #2f5fd0`)**: CVD adjacente PASS (pior par ΔE 9.0); floor de visão normal FALHA no par SMA 20×SMA 50 (ΔE 9.9 < 15) e os tons claros saem da banda — consequência direta da restrição de matiz. **Mitigação obrigatória** (regra do Design.md): espessura crescente por período (1.2/1.8/2.2 px), SMA contínua × EMA tracejada × BB pontilhada, e legenda com valores sempre visível. Recomendação de uso: no máximo 2–3 overlays ligados por vez (padrão: SMA 20 + SMA 50).
- **Cenários do modelo** (gelo/ciano/vermelho após a linha de corte): pares separados por posição (acima/abaixo do preço) além da cor; rótulos "melhor/esperada/pior" na ponta.

Auditoria de telas v2: os itens estruturais da auditoria v1 (links vs botões, aria-current, labels for/id, th focáveis, safe-area, tabular-nums, — reservado a nulo, mensagens genéricas de auth) foram mantidos no gerador v2. Novos pontos verificados: painel esquerdo do login usa `<a aria-label>` para GitHub/LinkedIn; chips "Em breve" (SMS/WhatsApp, Monte Carlo) não são focáveis nem clicáveis; texto sobre botão primário azul usa `#04070f` (7.4:1); glow limitado a 1 card por tela.
