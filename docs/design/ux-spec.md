# Especificação de UX — dashboard crypto-forecasting-app

Data: 2026-08-19 · Idioma da interface: PT-BR · Horários sempre em **UTC** · Stack alvo: Nuxt 4 + Nuxt UI v4 + Lightweight Charts v5 (ver `docs/plans/2026-08-19-front-end-architecture.md`).

Artefatos relacionados: [tokens.md](tokens.md) · [components.md](components.md) · [audit.md](audit.md) · [README.md](README.md) (direção visual + link do canvas).

Decisões tomadas com o usuário (2026-08-19): densidade **média/analítica**; tom **analítico sóbrio** (não "exchange"); aba **Previsões** visível e desabilitada ("em breve") + espaço reservado no gráfico; tabela 24h em **rota própria `/mercado`** (o dashboard mostra só o resumo 24h do ativo selecionado).

---

## 1. Conceito e assinatura visual

**"Observatório"** — o produto observa *snapshots* diários de um pipeline, não um mercado ao vivo. A UI é honesta sobre tempo em dois lugares, e esses dois elementos são a assinatura:

1. **Selo de snapshot** (toolbar): `● SNAPSHOT | Velas: 19 ago 00:00 UTC · há 6 h` — mono, caixa alta, ponto de estado (verde = dentro do esperado, âmbar = velho). É o único lugar onde "frescor" é declarado; nunca um "LIVE", nunca ticker piscando.
2. **Linha de corte** no gráfico: linha vertical tracejada (cor primária) após a última vela observada. À direita, área hachurada reservada à previsão ("previsão · em breve"). Quando `/forecasts` existir, a faixa projetada nasce exatamente dessa linha.

Todo o resto é quieto: neutros zinc, um acento índigo, verde/vermelho **só em dados**.

---

## 2. Mapa de rotas e navegação

| Rota | Layout | Guard | Conteúdo |
|---|---|---|---|
| `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/confirm` | `auth` (card centralizado) | `guest` (logado → `/`) | fluxos de auth |
| `/` | `default` | logado | Dashboard (gráfico + indicadores + resumo 24h do ativo) |
| `/mercado` | `default` | logado | Tabela-resumo 24h dos ~20 ativos |
| `/previsoes` | — | — | **não existe ainda**; item de nav desabilitado com badge "EM BREVE" |

Header (desktop, 56 px): logotipo `cf` + "crypto forecasting" · nav `Dashboard · Mercado · Previsões [EM BREVE]` · à direita: alternar tema, menu da conta (e-mail, Preferências, Sair).
Mobile (< 768 px): header compacto (logo, tema, conta) + **barra inferior** com `Dashboard · Mercado · Indicadores` (no dashboard) ou `Dashboard · Mercado · Previsões` (no mercado).

Estado na URL: `/?symbol=ETHUSDT&tf=1d` (sempre escrito de volta → links compartilháveis; restaurado após login expirado).

---

## 3. Fluxos de autenticação (mensagens exatas)

Regras gerais: mensagens **genéricas** (nunca revelar se um e-mail existe); botão primário único por tela; estado de carregamento no botão ("Entrando…"); erros em `role="alert"` logo acima dos campos; foco vai para o alerta ao aparecer.

### 3.1 Login `/login`
- Título **Entrar** · subtítulo "Use o e-mail e a senha da sua conta."
- Campos: E-mail · Senha (com "mostrar senha" e link "Esqueci a senha" à direita do label).
- Botão **Entrar**. Rodapé: "Não tem conta? **Criar conta**".
- Erro (qualquer causa de credencial): **"E-mail ou senha inválidos."** — idêntico para e-mail inexistente, senha errada e e-mail não confirmado*.
  - *Se o Supabase devolver "Email not confirmed", ainda assim mostrar a mesma mensagem + linha discreta: "Se você acabou de se cadastrar, confirme o e-mail pelo link que enviamos." (não confirma existência: só aparece como dica genérica).
- Erro de rede/API: "Não foi possível entrar agora. Tente novamente em alguns segundos."
- Query `?reason=expired` → banner neutro acima do card (`role="status"`, ícone relógio): **"Sua sessão expirou. Entre de novo para continuar — você voltará para onde estava."** Após login, redireciona para a rota salva (`saveRedirectToCookie`).

### 3.2 Cadastro `/signup`
- Título **Criar conta** · "Você receberá um link para confirmar o e-mail."
- Campos: E-mail · Senha (mín. 8; barra de força com rótulo textual "Força: fraca/razoável/boa") · Confirmar senha.
- Validação inline (ao sair do campo): "Informe um e-mail válido." · "A senha precisa ter pelo menos 8 caracteres." · "As senhas não coincidem."
- Botão **Criar conta** → sempre vai para `/confirm-email` (tela 3.3), mesmo se o e-mail já existir.
- Erro de rede: "Não foi possível criar a conta agora. Tente novamente."

### 3.3 Verifique seu e-mail (após cadastro)
- Ícone caixa de entrada · Título **Verifique seu e-mail**
- Texto: **"Se este e-mail for novo, enviamos um link de confirmação para `voce@exemplo.com`. O link vale por 24 horas."**
- Caixa: "Não chegou? Confira o spam. Você pode pedir outro link em `0:42`." → botão **Reenviar link** (desabilitado durante o cooldown de 60 s; ao reenviar: toast "Se este e-mail for novo, enviamos outro link.").
- Link "Voltar para entrar".

### 3.4 Callback `/confirm`
- Tela só com spinner + "Confirmando…". Sucesso → `/` (toast "E-mail confirmado. Bem-vindo."). `type=recovery` → `/reset-password`. Falha/timeout (8 s) → `/login` com banner "Não foi possível confirmar o link. Ele pode ter expirado — entre ou peça um novo."

### 3.5 Esqueci a senha `/forgot-password`
- Link "← Voltar" · Título **Esqueci a senha** · "Informe o e-mail da conta. Enviaremos um link para criar uma nova senha."
- Campo E-mail · Botão **Enviar link**.
- Após enviar (sempre, exista ou não): caixa `role="status"` com check: **"Se existir uma conta com este e-mail, você receberá um link em instantes."** Botão vira "Enviar de novo" com cooldown 60 s.

### 3.6 Redefinir senha `/reset-password`
- Título **Redefinir senha** · "Crie uma nova senha para `voce@exemplo.com`."
- Campos: Nova senha · Confirmar nova senha. Botão **Salvar nova senha**.
- Sucesso: toast **"Senha atualizada. Você já está conectado."** → `/`.
- Sem sessão de recuperação / link inválido: caixa "Link expirado ou inválido? **Peça um novo**." (vai para 3.5). Nunca dizer "usuário não encontrado".

### 3.7 Sessão expirada (em qualquer tela logada)
- 401 → refresh 1x → retry 1x → se falhar: `signOut()`, toast discreto **"Sessão expirada. Entre de novo para continuar."**, redirect `/login?reason=expired`, URL atual salva.

### 3.8 Sair
- Menu da conta → **Sair** → `/login` (sem toast; o contexto é óbvio). `clearNuxtData()`.

---

## 4. Dashboard `/`

### 4.1 Toolbar (linha abaixo do header)
Esquerda → direita:
1. **Seletor de ativo** (`USelectMenu`, busca): mostra `BTCUSDT` (mono, 500) + nome legível quando conhecido ("Bitcoin / Tether"). Menu: busca no topo (autofoco), cada item = símbolo + nome à esquerda, último preço + variação % (▲/▼) à direita (vem de `/tickers/24h`; se null → "—"). Rodapé: "20 ativos · top 20 por volume 24h" + dica de teclado `↑↓ · Enter`. Vazio: "Nenhum ativo encontrado". Enquanto `/symbols` carrega: botão com skeleton, desabilitado.
2. **Timeframe** (segmented, `15m | 1h | 1d`): `role="radiogroup"`, setas ←/→ trocam. Ao lado, subtítulo mono: `15m · últimos 7 dias` / `1h · últimos 30 dias` / `1d · histórico completo`.
3. (direita) **Selo de snapshot** (ver §6) + botão **Atualizar** (ícone + texto; spinner no ícone enquanto refaz as 3 requisições; não limpa o gráfico durante o refresh).

### 4.2 Gráfico (card principal, altura ≈ 65 % da viewport, mín. 520 px)
- Pane 0: candles + volume (escala própria, 18–20 % inferior) + overlays ligados. Pane 1: RSI 14 (faixas 30/70 tracejadas, zona 30–70 sombreada 4–5 %). Pane 2: MACD (linha, sinal, histograma divergente). Panes RSI/MACD só existem se o toggle estiver ligado; alturas 56 % / 22 % / 22 %.
- **Legenda** (canto superior esquerdo, sobreposta): linha 1 `BTCUSDT · 1h · 18 ago 14:00 UTC  A 113.250,1 M 113.900,0 m 112.800,5 F 113.512,3 Vol 1.284,5` (A/M/m/F = abertura/máx/mín/fechamento; fechamento na cor alta/baixa). Linha 2: um chip por overlay: swatch (cor + estilo de traço) · nome · valor mono. Sem crosshair: valores da última vela. Valor `null` → `—` + nota `warm-up até 16 ago` (data da primeira vela com valor) ou `warm-up · faltam N velas`.
- **Crosshair**: linhas tracejadas `text-dimmed`; etiquetas de preço/tempo em fundo `text-highlighted` com texto invertido; tempo sempre `DD mmm HH:MM` (15m/1h) ou `DD mmm AAAA` (1d).
- **Linha de corte** após a última vela + área hachurada (~11 % da largura) com rótulo `previsão · em breve` (desktop). Quando previsões existirem: faixa (80 %) e mediana tracejada na cor primária, partindo da linha.
- Rodapé do card (mono 11, dimmed): `Eixo em UTC · arraste para navegar · scroll para zoom · ┆ linha de corte = último dado observado` · à direita `720 velas · retenção 30 dias` (15m: `672 velas · retenção 7 dias`; 1d: `N velas · carregar mais antigo` como link quando houver mais de 1000).
- 1d com mais de 1000 velas: ao arrastar até a borda esquerda, botão flutuante "Carregar mais antigo" (busca com `end=` = primeira vela carregada); enquanto carrega, skeleton só na faixa esquerda.

### 4.3 Painel "Indicadores" (lateral direita, 264 px; desktop ≥ 1024 px)
- Grupos: **Sobre o preço** (SMA 20, SMA 50, SMA 200, EMA 12, EMA 26, Bollinger 20·2, Volume) · **Painéis abaixo** (RSI 14, MACD 12·26·9) · (futuro) **Modelo** (Previsão).
- Cada item: checkbox + swatch (cor + traço real: SMA contínuo, EMA tracejado, BB pontilhado, Volume barras) + nome. SMA 200 carrega nota `warm-up` quando a série atual ainda não tem 200 velas (título: "SMA 200 só existe a partir da 200ª vela").
- Rodapé: nota "Linhas começam só depois da janela de cálculo (warm-up). Não é erro." + ações **Restaurar padrão** / **Limpar tudo**.
- Padrão inicial: SMA 20, SMA 50, Volume, RSI 14, MACD ligados. Persistência: `localStorage` `cf:indicators:v1` (persistem entre sessões no mesmo navegador — o subtítulo do painel diz "persistem no navegador").
- Teclado: Tab percorre os checkboxes; Espaço alterna; o grupo tem `aria-label="Indicadores"`.
- Entre 768–1023 px: painel vira `UCollapsible` acima do gráfico ("Indicadores (5 ligados)"). < 768 px: `UDrawer` inferior aberto pelo item "Indicadores" da barra inferior, itens com `USwitch` de 44 px.

### 4.4 Resumo 24h do ativo (faixa abaixo do gráfico)
- Card com cabeçalho: `RESUMO 24H · BTCUSDT` · à direita `snapshot 19 ago 14:00 UTC · há 12 min · atualiza de hora em hora`.
- 7 stat tiles (desktop, 1 linha): Último preço · Variação 24h (`▲ +2.048,9 · +1,84 %`, cor alta/baixa) · Abertura · Máx / Mín · Preço médio pond. · Bid / Ask (+ sub "spread 0,003 %") · Volume 24h (`38.412 BTC`, sub `4,33 bi USDT · 4,21 mi trades`).
- Mobile: grade 2 colunas. Campo null → `—` (nunca 0), sub "sem snapshot". Sem snapshot nenhum para o ativo: faixa mostra só o cabeçalho + "Sem resumo 24h para este ativo ainda."
- Link "Ver todos os ativos →" leva a `/mercado`.

### 4.5 Primeiro acesso (onboarding leve)
- Sem `?symbol`: abre o **primeiro ativo de `/symbols` por volume 24h** (fallback: primeiro alfabético) em `1h`; escreve na URL.
- Card de dica ancorado ao painel de Indicadores (1 vez, `localStorage cf:onboarded:v1`): título **"Seu primeiro snapshot"** · texto "Abrimos o `BTCUSDT` em 1h. Escolha outro ativo no seletor ou ligue indicadores no painel ao lado — suas escolhas ficam salvas neste navegador." · botões **Não mostrar de novo** / **Entendi**. Item SMA 50 recebe um anel de foco visual enquanto a dica está aberta. `Esc` fecha.

---

## 5. Mercado `/mercado`

- Título **Mercado · resumo 24h** · subtítulo "Top 20 pares USDT por volume. Clique em um ativo para abri-lo no dashboard."
- Toolbar: filtro de texto ("Filtrar ativo…", filtra por símbolo/nome) · selo de snapshot do resumo 24h (`Resumo 24h: 19 ago 14:00 UTC · há 12 min · atualiza de hora em hora`) · **Atualizar**.
- Tabela (`UTable`): colunas Ativo (sticky) · Último · Var. 24h · Var. % · Preço médio · Abertura · Máxima · Mínima · Bid · Ask · Volume (base) · **Volume (USDT)** (ordem padrão, desc) · Trades. Todos numéricos alinhados à direita, mono tabular; cabeçalhos mono 11 caixa alta; `aria-sort` no `th` ativo; Enter/Espaço no cabeçalho ordena; nulls vão por último em qualquer ordenação.
- Variação: `▲ +1,84 %` verde / `▼ −0,62 %` vermelho / `+0,00 %` cinza sem seta (sem variação). `—` é reservado a **campo nulo** — nunca reutilizar para "sem variação". Nunca só cor.
- Linha: `tabindex="0"`, hover `bg-muted`, selecionada (ativo atual do dashboard) `bg-primary-soft`; Enter/clique → `navigateTo('/?symbol=X')` (mantém `tf` atual).
- Ativo sem snapshot: todas as células `—` (title "Sem snapshot recente para este ativo") + rótulo `sem dados` ao lado do símbolo; linha vai para o fim na ordenação padrão.
- Rodapé: "20 ativos · ordenado por volume (USDT) desc · cabeçalhos ordenáveis (Enter/Espaço)" · legenda `▲ alta · ▼ baixa · sem seta = sem variação · — = sem dados`.
- Mobile: lista de linhas (56 px, `<a>`): símbolo + "nome · vol 4,33 bi" à esquerda; último preço + variação à direita; botão "Volume ▾" abre menu de ordenação (Volume, Var. %, Último, Ativo). Filtro no topo. Sem colunas escondidas — quem quiser tudo usa o desktop (documentado na tela).

---

## 6. Frescor dos dados (regras do selo)

| Fonte | Cadência | Esperado | Limiar "velho" | Texto do selo |
|---|---|---|---|---|
| Candles + indicadores | 1×/dia (~00:05 UTC) | última vela `open_time` ≤ 26 h atrás | > 26 h | `Velas: 19 ago 00:00 UTC · há 6 h` |
| Resumo 24h | de hora em hora | snapshot ≤ 2 h | > 2 h | `Resumo 24h: 19 ago 14:00 UTC · há 12 min` |

- "há X" calculado a partir do `close_time`/`open_time` mais recente **do dado carregado** (não do horário do fetch). Formato: `há 12 min` (< 1 h), `há 6 h`, `há 31 h`, `há 3 d`.
- Estado **fresh**: ponto verde, borda padrão. Estado **stale**: ícone de alerta âmbar, borda/fundo âmbar, texto `Velas atualizadas em 18 ago 00:00 UTC · há 31 h` + `UAlert` inline acima do gráfico: **"Dados mais antigos que o esperado.** Os candles deveriam ter sido atualizados há ~7 h (00:05 UTC). O gráfico continua utilizável; os valores podem não refletir o último dia. **Tentar novamente**". O gráfico nunca é bloqueado por stale.
- Tooltip do selo (hover/focus): "Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real."
- Enquanto carrega: selo com skeleton no texto. Erro: selo neutro com "—".
- Nunca usar as palavras "ao vivo", "live", "tempo real" na UI.

---

## 7. Estados por bloco

| Bloco | Loading | Vazio | Erro | Warm-up | Stale |
|---|---|---|---|---|---|
| Seletor de ativo | botão skeleton desabilitado | "Nenhum ativo rastreado ainda" | botão com ícone de alerta + tooltip "Não foi possível carregar os ativos. Tentar novamente" | — | — |
| Gráfico | skeleton com a forma dos panes + legenda em barras + "Carregando BTCUSDT · 1h…" (mantém o gráfico anterior visível e esmaecido se for troca de ativo/tf — sem flash) | título **Sem dados para PEPEUSDT em 1h** · "Este ativo está na lista dos top 20, mas ainda não tem candles neste timeframe. Tente outro timeframe ou volte depois da próxima coleta (00:05 UTC)." · ações **Ver em 1d** / **Escolher outro ativo** | **Não foi possível carregar o gráfico** · "A API não respondeu. Tente de novo em alguns segundos." · **Tentar novamente** + detalhe mono `GET /klines/1h · 503` | linhas começam onde existe valor (`WhitespaceData`); legenda `—` + `warm-up até <data>`; nota fixa no painel; **nunca zero, nunca reta em 0** | selo âmbar + alerta (§6); gráfico visível |
| Indicadores (features) | overlays aparecem quando chegam; candles não esperam features | painel mostra "Indicadores indisponíveis para este ativo/timeframe" (toggles ficam ligados, séries não desenham) | alerta inline dentro do painel "Indicadores não carregaram. Tentar novamente" — candles seguem | idem acima | idem |
| Resumo 24h (faixa) | tiles com skeleton | "Sem resumo 24h para este ativo ainda." | "Resumo 24h indisponível. Tentar novamente" | campos null → `—` | cabeçalho âmbar `há 3 h · esperado ≤ 2 h` |
| Tabela Mercado | 8 linhas skeleton | "Nenhum snapshot disponível. Tente novamente em alguns minutos." | `ErrorState` no lugar da tabela + retry | — | selo âmbar no topo |
| Sessão | — | — | 401 → redirect (§3.7) | — | — |
| Parâmetros inválidos (422) | — | — | tf inválido na URL → corrige para `1h` silenciosamente; símbolo desconhecido → vazio (API devolve `200 []`) | — | — |

Regra geral: o **container não muda de tamanho nem de lugar** entre estados; só o conteúdo interno. Mensagens de erro dizem o que aconteceu e o que fazer; não pedem desculpas; não são vagas.

---

## 8. Responsividade

| Faixa | Layout |
|---|---|
| ≥ 1280 | header + toolbar em 1 linha; gráfico + painel lateral 264 px; faixa 24h em 7 tiles |
| 1024–1279 | painel lateral 232 px; legenda OHLC abrevia (A/M/m/F já são abreviações) |
| 768–1023 | painel vira colapsável acima do gráfico; toolbar quebra em 2 linhas (seletor+tf / selo+atualizar); faixa 24h 4+3 tiles |
| < 768 (mobile) | header compacto; seletor (40 px) + tf; selo + atualizar; gráfico 430 px com **RSI apenas por padrão** (MACD desliga em mobile na 1ª visita; usuário pode religar); legenda em 3 linhas; faixa 24h em grade 2 col; barra inferior; toggles em drawer; tabela Mercado vira lista |

Gráfico no mobile: pan por toque (1 dedo), pinch para zoom; crosshair por toque longo; sem scroll da página enquanto arrasta dentro do gráfico (`touch-action: none` só no canvas). Eixo de tempo com 4 rótulos.

---

## 9. Acessibilidade

- **Contraste**: texto ≥ 4.5:1 (`text-muted` light #52525b sobre #fafafa = 7.0:1; dark #a1a1aa sobre #18181b = 7.2:1); alta/baixa sobre superfície ≥ 3:1 e sempre com ▲/▼ ou sinal; EMA 12/26 em light abaixo de 3:1 como linha → valores sempre na legenda (regra de alívio do `dataviz`).
- **Foco visível**: anel 2 px primário com offset 2 px em botões, links, inputs, linhas de tabela, toggles, itens do seletor, badge do selo (focável para abrir tooltip).
- **Teclado**: seletor = combobox (↑↓, Enter, Esc, digitação filtra); timeframe = radiogroup (←→); toggles = checkboxes (Espaço); tabela = cabeçalhos focáveis ordenam, linhas focáveis abrem; drawer mobile prende foco e fecha com Esc; dica de onboarding é `role="dialog"` não modal, Esc fecha.
- **Gráfico (canvas)**: `aria-label` descritivo no container ("Gráfico de candles BTCUSDT 1h, 720 velas, de 20 jul a 19 ago 2026 UTC, com SMA 20 e SMA 50"), e **tabela alternativa** acessível via link "Ver como tabela" (modal com OHLCV + indicadores das últimas 50 velas, `UTable`) — é a saída para leitores de tela e também para conferência de números.
- **Movimento**: nenhuma animação essencial; skeleton shimmer e transições respeitam `prefers-reduced-motion`.
- **Rótulos**: todos os inputs com `<label>`; botões só-ícone com `aria-label` (Alternar tema, Atualizar, Conta, Fechar, Mostrar senha); `aria-live="polite"` no selo quando muda de fresh→stale e nos toasts.
- **Idioma**: `lang="pt-BR"`; números em formato pt-BR (`113.512,3`), horários `DD mmm HH:MM UTC`.
- **Tamanho de alvo**: ≥ 32 px desktop, ≥ 44 px mobile.
- **Preferência "Velas de alta vazadas"** (Conta → Preferências): alternativa para daltonismo deutan; persiste em `localStorage`.

---

## 10. Microcopy de referência (coleção)

| Contexto | Texto |
|---|---|
| Selo fresh (candles) | `SNAPSHOT | Velas: 19 ago 00:00 UTC · há 6 h` |
| Selo stale | `SNAPSHOT | Velas atualizadas em 18 ago 00:00 UTC · há 31 h` |
| Selo resumo 24h | `Resumo 24h: 19 ago 14:00 UTC · há 12 min · atualiza de hora em hora` |
| Tooltip do selo | "Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real." |
| Nota warm-up (legenda) | `— warm-up até 16 ago` / `— warm-up · faltam 140 velas` |
| Nota warm-up (painel) | "Linhas começam só depois da janela de cálculo (warm-up). Não é erro." |
| Subtítulo de timeframe | `15m · últimos 7 dias` · `1h · últimos 30 dias` · `1d · histórico completo` |
| Rodapé do gráfico | `Eixo em UTC · arraste para navegar · scroll para zoom · ┆ linha de corte = último dado observado` |
| Área reservada | `previsão · em breve` |
| Botão atualizar (carregando) | `Atualizando…` |
| Toast após refresh manual | "Dados atualizados. Snapshot de 19 ago 00:00 UTC." (se nada mudou: "Nenhum snapshot novo desde 00:00 UTC.") |
| Toggle restaurar | "Indicadores restaurados ao padrão." |
| Vazio seletor | "Nenhum ativo encontrado" |
| Login erro | "E-mail ou senha inválidos." |
| Cadastro pós-envio | "Se este e-mail for novo, enviamos um link de confirmação para …" |
| Esqueci pós-envio | "Se existir uma conta com este e-mail, você receberá um link em instantes." |
| Sessão expirada | "Sua sessão expirou. Entre de novo para continuar — você voltará para onde estava." |
| Senha salva | "Senha atualizada. Você já está conectado." |

---

## 11. Ajustes pós-auditoria (2026-08-19)

- "Limpar tudo" (toggles) não abre modal: aplica e mostra toast com **Desfazer** (5 s).
- Todo símbolo de ativo no DOM leva `translate="no"`.
- Barra inferior mobile: itens de navegação são links (`<a aria-current>`), "Indicadores" é botão (`aria-haspopup="dialog"`); `padding-bottom: max(8px, env(safe-area-inset-bottom))`; `scroll-padding-bottom` igual à altura da barra para o foco nunca ficar coberto.
- `h1` visualmente oculto em `/` ("Dashboard"); `text-wrap: balance` nos títulos.
- Fontes IBM Plex self-hosted no build estático com `font-display: swap` (o CSP do deploy pode não liberar Google Fonts).
