# CRYPTO FORECASTING — Design System e UX

Versão 3 · **Observatório Vivo** · 2026-08-23 · status: aprovado para implementação.

## Autoridade deste documento

Este arquivo é a **única fonte normativa de UI/UX** do produto. Antes de implementar, revisar ou gerar uma tela, leia-o por inteiro.

- Referências visuais atuais: `docs/design/mockups/current/`.
- Os PNGs definem composição, atmosfera e hierarquia. Este arquivo define comportamento, conteúdo, tokens, responsividade e acessibilidade.
- Em qualquer divergência entre imagem e texto, **este arquivo vence**.
- Documentos e mockups anteriores ao v3 não fazem parte da especificação atual.
- A stack continua Vue 3 + Nuxt 4 + Nuxt UI v4/Tailwind v4 + Lightweight Charts v5. Este documento não muda decisões de arquitetura dos ADRs.

## 1. Produto e princípios

CRYPTO FORECASTING é uma plataforma de **forecasting, analytics e inteligência de mercado**, não uma exchange nem um terminal em tempo real.

### 1.1 Assinatura do produto

1. **Paisagem de dados:** curvas, partículas, topografia e profundidade representam probabilidade e fluxo.
2. **Leitura antes da exploração:** Home e Previsões começam com narrativa editorial; gráficos e tabelas vêm depois.
3. **Snapshot honesto:** candles e indicadores atualizam uma vez por dia; o resumo 24h, de hora em hora. Nunca usar “live”, “ao vivo” ou “tempo real”.
4. **Linha de corte:** todo gráfico que mistura observado e previsto marca explicitamente o último dado observado.
5. **Cenários, não recomendações:** toda superfície de previsão inclui o disclaimer definido na seção 13.

### 1.2 Direção visual

O conceito **Observatório Vivo** substitui o Dark-Tech baseado em cards de vidro. A experiência deve parecer editorial, imersiva e precisa.

- Seções são demarcadas por mudança de tom, macroespaço e movimento.
- Conteúdo principal flui sem moldura. Superfícies aparecem apenas quando têm função: input, popover, modal, estado ou foco.
- Tabelas usam divisores discretos e linhas abertas; não recebem card externo.
- Gráficos são paisagens full-bleed dentro da área da página; não recebem moldura luminosa.
- Glows são iluminação atmosférica localizada, nunca contorno de painel.
- A interface dark-only evita preto sólido contínuo: o fundo sempre possui profundidade tonal e microtextura.

## 2. Marca e linguagem

### 2.1 Nome

A marca aparece sempre como **CRYPTO FORECASTING**, em caixa alta, inclusive no header, Login, mobile, títulos de documento e metadados.

### 2.2 Tom de voz

- Analítico, direto e sóbrio.
- Frases curtas; números carregam a evidência.
- Não usar linguagem de hype, compra, venda, ganho garantido ou urgência.
- Usar o vocabulário de `CONTEXT.md`: ativo, símbolo, timeframe, vela/candle, indicador, warm-up, snapshot e previsão.
- Símbolos como `BTCUSDT` ficam em caixa alta e recebem `translate="no"`.

## 3. Tipografia

### 3.1 Família

- **Geist** é a fonte global da interface e dos títulos.
- **Geist Mono** é permitida apenas para números tabulares, símbolos, UTC, eixos e microcopy técnica.
- Carregar por Google Fonts conforme o briefing ou self-host dos WOFF2 com `font-display: swap`; preferir self-host em produção.
- Fallback: `system-ui, sans-serif` para Geist e `ui-monospace, Consolas, monospace` para Geist Mono.

### 3.2 Escala desktop

| Papel | Tamanho / linha | Peso | Regras |
|---|---:|---:|---|
| Display editorial | `64–80 / .98` | 520–620 | máximo 3 linhas; tracking `−0.035em` |
| H1 de página | `36–44 / 1.05` | 600 | `text-wrap: balance` |
| H2 de seção | `24–32 / 1.12` | 580 | amplo espaço acima |
| Título funcional | `16–18 / 1.3` | 600 | gráfico, formulário, estado |
| Corpo | `15–18 / 1.55` | 400 | largura ideal 52–68 caracteres |
| UI | `13–14 / 1.45` | 450–550 | controles e tabelas |
| Eyebrow | `11–12 / 1.2` | 550 | caixa alta, tracking `0.12em` |
| Dados | `13–16 / 1.3` | 450–550 | Geist Mono, `tabular-nums` |

No mobile, displays usam `44–56 px`, H1 `30–36 px` e corpo mínimo `15 px`.

## 4. Cores e tokens

### 4.1 Fundos e texto

| Token | Valor | Uso |
|---|---|---|
| `--cf-bg-0` | `#050811` | fundo profundo |
| `--cf-bg-1` | `#081426` | navy mineral |
| `--cf-bg-2` | `#0A1721` | petróleo de seções analíticas |
| `--cf-surface` | `rgba(11,20,34,.78)` | inputs, popovers, modais e estados |
| `--cf-surface-solid` | `#0B1422` | fallback sem transparência |
| `--cf-text-hi` | `#F3F7FC` | títulos e valores principais |
| `--cf-text` | `#DCE5F1` | texto padrão |
| `--cf-text-muted` | `#9EACC0` | descrição e labels |
| `--cf-text-dim` | `#66788F` | eixos, placeholders e linhas auxiliares |
| `--cf-hairline` | `rgba(216,231,245,.12)` | divisores funcionais |
| `--cf-hairline-soft` | `rgba(216,231,245,.07)` | grade e separação de linhas |

### 4.2 Acentos semânticos

| Token | Valor | Regra |
|---|---|---|
| `--cf-electric` | `#3E86F7` | ação, foco, navegação ativa e link |
| `--cf-cyan` | `#5FC4FF` | IA, cenário-base e informações de previsão |
| `--cf-ice` | `#DBE7F5` | estrutura, alta de candle e dados observados |
| `--cf-down` | `#E5484D` | queda, pior cenário e erro |
| `--cf-best` | `#62F6A2` | **exclusivo** do melhor cenário no Monte Carlo |
| `--cf-warn` | `#D6B25E` | stale e atenção não destrutiva |

Regras:

- Positivos comuns usam gelo ou ciano; verde não é a cor global de alta.
- `--cf-best` não aparece em botões, candles, tabelas comuns ou vídeo do Login.
- Roxo, rosa, laranja e gradientes multicoloridos não pertencem ao sistema atual.
- Cor nunca é o único canal: usar sinal, posição, rótulo, traço ou ícone.

### 4.3 Fundos

Cada página combina os três fundos em gradientes de baixo croma. Base recomendada:

`radial-gradient(1100px 650px at 62% 12%, rgba(30,76,112,.18), transparent 66%), linear-gradient(145deg, #050811 0%, #081426 55%, #0A1721 100%)`.

Aplicar microgrão fixo de `2–3%` de opacidade e `pointer-events: none`. A textura não pode prejudicar texto, tabela ou gráfico.

## 5. Espaço, grade e superfícies

- Grade base: `4 px`.
- Largura: fluida, com margem desktop `40–56 px`; `24–32 px` em tablet; `16–20 px` no mobile.
- Header desktop: `72 px`; mobile: `60 px`.
- Espaço vertical entre seções: `120–176 px` desktop; `72–96 px` mobile.
- Seções narrativas podem usar `min-height: calc(100dvh - 72px)`; nunca `100vh` fixo.
- Controles: raio `8 px`; popovers/modais: `12 px`; chips de status: `999 px` somente quando status realmente pede cápsula.
- Alvo interativo: mínimo `36 px` desktop e `44 px` mobile.
- Sombra: difusa e curta, apenas para elementos flutuantes. Conteúdo de página não recebe sombra.
- Blur: apenas header/overlay fixo, popover ou modal. Evitar blur em grandes áreas roláveis.

### 5.1 Regra de containers

Use superfície delimitada somente para:

- campos de formulário;
- menus, popovers, tooltips e modais;
- mensagens de erro/estado que precisam separar-se do conteúdo;
- painel de indicadores quando o espaço exige um dock funcional.

Narrativa, resumo da rodada, insights, tabelas, métricas e Monte Carlo permanecem abertos no layout.

## 6. Navegação e app shell

### 6.1 Desktop

Header fino, integrado ao fundo, com uma única hairline inferior:

- esquerda: **CRYPTO FORECASTING**;
- centro: `INÍCIO · GRÁFICOS · PREVISÕES · MERCADO`;
- direita: nome do usuário e menu da conta.

Item ativo: texto `--cf-electric` e sublinhado fino animado. Não usar pills em torno dos itens. Dark-only: não há toggle de tema.

### 6.2 Mobile

- Header: marca abreviada apenas se faltar largura, mas o nome acessível continua **CRYPTO FORECASTING**.
- Barra inferior: `INÍCIO · GRÁFICOS · PREVISÕES · MERCADO`, com safe area.
- Controles contextuais de gráfico abrem em drawer inferior.
- `scroll-padding-bottom` considera a barra para não cobrir foco.

### 6.3 Estado na URL

Símbolo e timeframe permanecem compartilháveis (`?symbol=ETHUSDT&tf=1d`). Restaurar a URL após reautenticação.

## 7. Movimento

### 7.1 Curvas e duração

- Entrada de seção: `700–900 ms`, `cubic-bezier(0.32,0.72,0,1)`.
- Microinteração: `180–280 ms`, `cubic-bezier(0.2,0.8,0.2,1)`.
- Elementos entram por `opacity` e `transform`; não animar propriedades de layout.
- Botões comprimem até `scale(.98)` ao pressionar.
- Sublinhados e linhas de dados crescem pela origem correta, evitando fades genéricos.

### 7.2 Scroll

- Títulos narrativos podem ficar brevemente pinned enquanto a visualização se revela.
- O fundo interpola de navy para petróleo entre seções, sem saltos de cor.
- Listas de dados entram com atraso de `40–70 ms` por linha.
- Movimento não pode atrasar acesso ao conteúdo nem bloquear interação.

### 7.3 Redução de movimento

Com `prefers-reduced-motion: reduce`:

- vídeo do Login usa poster estático;
- trajetórias e gráficos aparecem completos;
- scroll pinning e parallax são removidos;
- skeleton não usa shimmer contínuo;
- nenhum conteúdo ou estado depende da animação.

## 8. Login e autenticação

### 8.1 Login `/login`

Referência: `mockups/current/01-login-imersivo.png`.

- Marca pequena no topo esquerdo, margem ampla; nenhum logo grande.
- Torus ocupa a região central/esquerda e pode cruzar o centro, preservando contraste do formulário.
- Formulário no terço direito, integrado ao fundo; não usar card externo.
- Um véu tonal localizado atrás dos campos é permitido.
- Campos mantêm label visível, foco elétrico de 2 px e contraste AA.
- Rodapé técnico: `Dados da Binance · snapshots diários · horários em UTC`.

Texto:

- título: `Entrar`;
- subtítulo: `Use o e-mail e a senha da sua conta.`;
- campos: `E-mail`, `Senha`;
- link: `Esqueci a senha`;
- botão: `Entrar`;
- rodapé: `Não tem conta? Criar conta`.

### 8.2 Vídeo do Login — decisão final

**Escolha aprovada: Abstract Quantum Probability Torus Loop.**

O torus representa probabilidade, cenários e fluxo contínuo. A alternativa “Blockchain Data Node Sphere” não deve ser usada: ela desloca a leitura para infraestrutura blockchain/security e sugere transmissão em tempo real.

Especificação:

- duração: `12 s` preferencial, aceitável `10–15 s`;
- loop perfeitamente cíclico;
- composição 16:9, entrega principal `2560×1440` ou `1920×1080`;
- torus central/esquerdo, centro geométrico aproximadamente em `38% x 51%`;
- rotação vertical lenta + fluxo Moiré interno; a posição do primeiro e último frame deve coincidir;
- milhares de filamentos de fibra óptica/vidro fosco, partículas discretas e profundidade volumétrica;
- paleta: ciano elétrico, azul elétrico, branco-gelo e petróleo; convergências podem piscar em branco-gelo;
- brilho sutil e interno; preservar detalhes dos filamentos e pretos profundos;
- câmera estável, 50 mm equivalente com leve grande-angular, DOF moderada; evitar vertigem e zoom contínuo;
- sem texto, números binários, logos, moedas, roxo, amarelo ou verde;
- área direita mais calma para o formulário.

Prompt final para Higgsfield/Cinema Studio:

> High-end 3D motion graphics of an abstract quantum probability torus, positioned center-left in a deep mineral navy environment. The torus is hollow and formed by thousands of ultra-fine mathematical filaments, optical-fiber glass lines and sparse particles. It rotates slowly around its vertical axis while the filaments flow through the surface in a smooth Moiré probability-wave motion, contracting and expanding with controlled kinetic rhythm. Perfect 12-second seamless loop: first and last frames match exactly. Electric cyan, electric blue and ice-white light only, over a near-black to deep-petrol radial gradient with subtle data dust and restrained volumetric haze. Internal light, soft refraction, crisp filaments, no plastic appearance, no excessive bloom. Stable cinematic camera, medium close-up, 50mm equivalent with a slightly wide feeling, moderate depth of field. Keep the right third visually calm and dark for a login form. No text, binary numbers, logos, coins, blockchain nodes, purple, yellow, green, camera orbit or abrupt glitches.

Entrega web:

- WebM e MP4 otimizados, sem áudio;
- `autoplay`, `muted`, `loop`, `playsinline`;
- poster estático derivado do mesmo frame;
- pausar quando a aba estiver oculta;
- no mobile e em redução de movimento, usar poster ou variante leve.

### 8.3 Demais telas de autenticação

Cadastro, confirmação, recuperação e redefinição usam o mesmo fundo, porém com torus estático e mais discreto. Formulário central/direito sem card externo; mensagens de estado podem usar superfície funcional.

Mensagens normativas:

- login inválido: `E-mail ou senha inválidos.`;
- rede no login: `Não foi possível entrar agora. Tente novamente em alguns segundos.`;
- sessão: `Sua sessão expirou. Entre de novo para continuar — você voltará para onde estava.`;
- cadastro: `Se este e-mail for novo, enviamos um link de confirmação para {email}. O link vale por 24 horas.`;
- esqueci senha: `Se existir uma conta com este e-mail, você receberá um link em instantes.`;
- confirmação falhou: `Não foi possível confirmar o link. Ele pode ter expirado — entre ou peça um novo.`;
- senha salva: `Senha atualizada. Você já está conectado.`.

Nunca confirmar se um e-mail existe.

## 9. Home `/`

### 9.1 Abertura narrativa

Referência: `mockups/current/02-home-abertura-narrativa.png`.

Ordem:

1. `BEM-VINDO NOVAMENTE, {NOME}`;
2. `As principais mudanças no mercado desde o seu último acesso`;
3. timestamp do último acesso;
4. **Market Delta Lens** como estrutura editorial: SVG aberto, sem card, com uma linha temporal e trajetórias abstratas que se expandem do último acesso até o snapshot atual;
5. label `LEITURA DO DIA`;
6. manchete narrativa;
7. explicação em texto corrido;
8. snapshot integrado à linha de base.

“Leitura do dia” nunca recebe card. No primeiro acesso, o título contextual vira `O mercado nas últimas 24 h`.

A Market Delta Lens é estrutural, não quantitativa: não exibe valores nem sugere medições ausentes. Ao entrar, a linha temporal aparece primeiro, as trajetórias desenham da esquerda para a direita em `800–1100 ms`, os pontos surgem em sequência e a convergência final pulsa uma única vez. Em redução de movimento, o SVG aparece completo e estático.

### 9.2 Mudanças do mercado

Referência: `mockups/current/03-home-mudancas-mercado.png`.

Três faixas abertas:

1. `MAIOR VOLATILIDADE` — ATR 14 relativo;
2. `GAP REAL × PROJEÇÃO` — exclusivo de IA, com `IA · v0 · EM VALIDAÇÃO` enquanto necessário;
3. `MAIOR VOLUME` — volume 24h versus média de 7 dias.

Cada faixa usa numeral estrutural, título, explicação e até cinco linhas. Uma trajetória contínua pode atravessar as três leituras. Clique/teclado em ativo abre `/graficos?symbol=X`.

No mobile, as faixas empilham sem cards; a trajetória vira um fio vertical de continuidade. Mostrar 2 itens por faixa e ação `Ver top 5`.

## 10. Gráficos `/graficos`

- Toolbar: ativo, timeframe, snapshot e atualizar.
- Gráfico principal ocupa a largura disponível; painel de indicadores é um dock funcional lateral, não um card decorativo.
- Candles, volume, RSI e MACD seguem a especificação da seção 14.
- Após a linha de corte, melhor/base/pior começam exatamente no último dado observado.
- Resumo 24h abaixo do gráfico é uma faixa aberta com divisores verticais; não usar stat tiles encaixotados.
- Rodapé: `Eixo em UTC · arraste para navegar · scroll para zoom · linha de corte = último dado observado`.
- Indicadores persistem no navegador. Ações: `Restaurar padrão` e `Limpar tudo`; limpar mostra toast com `Desfazer` por 5 s.

Responsividade:

- `≥1024`: dock lateral;
- `768–1023`: indicadores em colapsável acima do gráfico;
- `<768`: drawer inferior; gráfico com 430 px mínimos, RSI ligado e MACD desligado no primeiro acesso.

## 11. Previsões `/previsoes`

### 11.1 Resumo e horizontes

Referência: `mockups/current/04-previsoes-resumo-horizontes.png`.

- `Resumo da rodada` é texto aberto, sem card.
- Versão, MAE e direção ficam em faixa tipográfica com hairlines, sem pills.
- Quatro arcos partem de `DADO OBSERVADO`: diário, semanal, mensal e anual.
- O aumento da abertura visual representa o crescimento da incerteza.

### 11.2 Tabela de cenários

Referência: `mockups/current/05-previsoes-tabela-cenarios.png`.

- Full-bleed dentro das margens; nenhum card externo ou cantos arredondados.
- Colunas: ativo, preço real, diário, semanal, mensal, anual e confiança.
- Cabeçalhos e números usam Geist Mono/tabular.
- Linha ativa recebe wash horizontal discreto.
- Negativos em vermelho; cenário-base/confiança em ciano; demais positivos em gelo/ciano.
- Null é sempre `—`; zero real é `0`.
- No mobile, cada ativo vira bloco de linha expansível sem card; diário e confiança ficam visíveis, horizontes adicionais abrem por disclosure.

### 11.3 Monte Carlo

Referência: `mockups/current/06-previsoes-monte-carlo.png`.

- Visualização full-bleed, sem container emoldurado.
- Esquerda: histórico observado; linha de corte `ÚLTIMO DADO OBSERVADO`.
- Direita: 1.000 trajetórias. Se desempenho exigir, a renderização pode amostrar visualmente, mas a UI informa a quantidade real simulada.
- Animação no load/reload: trajetórias desenham da esquerda para a direita em ondas escalonadas durante `1,6–2,2 s`.
- Ao terminar, destacar exatamente três caminhos:
  - melhor: `--cf-best` verde;
  - base/médio: `--cf-cyan`;
  - pior: `--cf-down`.
- As outras trajetórias permanecem gelo-azul com baixa opacidade.
- Faixa de incerteza nasce estreita na linha de corte e abre com o horizonte.
- Rótulos das três trajetórias entram somente após o desenho.
- Controles: ativo, horizonte e `Reiniciar simulação`.
- Interação: pan, zoom, crosshair e tooltip acessíveis; oferecer tabela alternativa.

## 12. Mercado `/mercado` e Preferências `/preferencias`

### 12.1 Mercado

- Aplicar a linguagem da tabela de cenários: full-bleed, hairlines, linha ativa em wash.
- Colunas desktop: ativo, último, variação 24h, variação %, preço médio, abertura, máxima, mínima, bid, ask, volume base, volume USDT e trades.
- Ordem padrão: volume USDT decrescente; nulls sempre por último.
- `▲ +1,84 %`, `▼ −0,62 %`, `+0,00 %` sem seta e `—` apenas para ausência de dado.
- Mobile: lista de 56 px com símbolo/nome/volume à esquerda e último/variação à direita.

### 12.2 Preferências

- Página em seções abertas separadas por macroespaço e hairlines: Dados pessoais, Acessibilidade e Notificações.
- Campos recebem superfície funcional; cada seção não recebe card externo.
- E-mail é somente leitura.
- Telefone: `type="tel"`, `autocomplete="tel"`, máscara BR e persistência E.164.
- Notificações: gaps, volume, volatilidade e novas rodadas; E-mail ativo, SMS/WhatsApp `Em breve` quando indisponíveis.
- Acessibilidade: `Velas de alta preenchidas`.

## 13. Frescor, estados e microcopy

### 13.1 Snapshot

| Fonte | Cadência | Stale | Texto-base |
|---|---|---|---|
| Candles + indicadores | 1×/dia, ~00:05 UTC | `>26 h` | `SNAPSHOT · Velas: 19 ago 00:00 UTC · há 6 h` |
| Resumo 24h | de hora em hora | `>2 h` | `SNAPSHOT · Resumo 24h: 19 ago 14:00 UTC · há 12 min` |

Stale usa dourado + ícone + texto. O gráfico continua disponível. Tooltip: `Candles e indicadores atualizam 1x/dia (~00:05 UTC); resumo 24h de hora em hora. Nada é tempo real.`

### 13.2 Estados obrigatórios

| Estado | Regra |
|---|---|
| Loading | manter geometria; skeleton; ao trocar ativo, preservar dado anterior esmaecido até o novo chegar |
| Vazio | explicar o motivo provável e oferecer próxima ação |
| Erro | dizer o que falhou e oferecer `Tentar novamente`; detalhe técnico opcional em Geist Mono |
| Warm-up | desenhar gap, nunca zero; legenda `— warm-up até {data}` ou `— warm-up · faltam N velas` |
| Stale | aviso inline sem bloquear conteúdo |
| Sessão expirada | refresh 1×, retry 1×, sign out e voltar ao Login preservando a rota |

Mensagens do gráfico:

- vazio: `Sem dados para {SYMBOL} em {TF}`;
- descrição: `Este ativo está na lista dos top 20, mas ainda não tem candles neste timeframe.`;
- erro: `Não foi possível carregar o gráfico. A API não respondeu. Tente de novo em alguns segundos.`;
- indicador: `Linhas começam só depois da janela de cálculo (warm-up). Não é erro.`.

### 13.3 Previsões

Enquanto previsões não existirem, nunca inventar números. Mostrar: `O modelo ainda não publicou previsões para este ativo.`

Disclaimer normativo: `Leia as previsões como cenários, não como recomendação de compra ou venda.`

## 14. Visualização de dados

### 14.1 Séries

| Série | Cor | Traço |
|---|---|---|
| Vela alta | `#DBE7F5`, corpo `rgba(219,231,245,.10)` | vazada, contorno 1 px |
| Vela baixa | `#E5484D` | preenchida |
| SMA 20 / 50 / 200 | `#4F8FF7` / `#2596BE` / `#C8D9EF` | contínua `1.2 / 1.8 / 2.2 px` |
| EMA 12 / 26 | `#8AB8FF` / `#2F5FD0` | tracejada `1.2 / 1.8 px` |
| Bollinger | `rgba(200,217,239,.55)` | pontilhada; banda 5% |
| Volume | gelo 28% / vermelho 30% | histograma |
| RSI | `#4F8FF7` | contínua; faixas 30/70 |
| MACD linha / sinal | `#4F8FF7` / `#DBE7F5` | histograma gelo/vermelho 45% |
| Melhor Monte Carlo | `#62F6A2` | 2–2.4 px |
| Base Monte Carlo | `#5FC4FF` | 2–2.4 px |
| Pior Monte Carlo | `#E5484D` | 2–2.4 px |

Legenda com valores é obrigatória. Diferenciar séries também por espessura, padrão de traço, posição e rótulo.

### 14.2 Gráfico acessível

- Container recebe `aria-label` com ativo, timeframe, quantidade e datas.
- Link `Ver como tabela` abre as últimas 50 velas/linhas em tabela acessível.
- Pan/zoom por toque possuem alternativas por teclado e botões.
- `touch-action: none` somente no canvas.
- Valores usam `Intl.NumberFormat('pt-BR')`; datas sempre UTC.

## 15. Componentes e comportamento

Use Nuxt UI como base funcional, customizando a aparência para esta especificação.

| Componente | Base sugerida | Regra visual/UX |
|---|---|---|
| AppHeader | `UHeader`, `UNavigationMenu`, `UDropdownMenu` | fundo integrado, hairline, nav sem pills |
| SymbolSelector | `USelectMenu` | busca, símbolo/nome/último/variação; superfície funcional |
| TimeframeToggle | `UTabs` ou `URadioGroup` | compacto; ativo por linha/wash, não card |
| SnapshotBadge | `UTooltip` + conteúdo próprio | texto de baseline; cápsula apenas em toolbar apertada |
| ChartPanel | wrapper próprio + Lightweight Charts | sem `UCard`; estados preservam tamanho |
| IndicatorToggles | `UCheckboxGroup`, `UDrawer` mobile | dock funcional; fieldsets e legends |
| Summary24hStrip | grid próprio | aberto, divisores verticais, sem tiles emoldurados |
| ForecastTable / MarketTable | `UTable` | full-bleed, hairlines e row wash |
| AuthForm | `UForm`, `UFormField`, `UInput` | sem AuthCard externo; erro ligado ao campo |
| EmptyState / ErrorState | componentes próprios | superfície somente quando necessária; `role=status/alert` |
| MonteCarloChart | canvas/WebGL ou SVG otimizado | redução de movimento e tabela alternativa |

Estado assíncrono é uma variante única (`idle | loading | empty | error | ready`), evitando combinações booleanas conflitantes.

## 16. Responsividade e acessibilidade

### 16.1 Breakpoints

| Faixa | Comportamento |
|---|---|
| `≥1280` | composição completa, macroespaço e tabelas integrais |
| `1024–1279` | margens menores, dock de indicadores reduzido |
| `768–1023` | toolbar em duas linhas, indicadores colapsáveis |
| `<768` | fluxo de uma coluna, barra inferior, drawers, tabelas adaptadas |

### 16.2 Requisitos

- Contraste WCAG AA: texto comum `≥4.5:1`; texto grande e elementos gráficos `≥3:1`.
- Foco visível: `2 px solid --cf-electric`, offset `2 px`.
- Navegação completa por teclado: combobox, timeframe, toggles, ordenação, linhas, drawers e modais.
- Inputs sempre com label; e-mail usa `type=email`, `autocomplete=email`, `spellcheck=false`; senha usa autocomplete correto; paste permitido.
- Botões só-ícone recebem `aria-label`; ícones decorativos recebem `aria-hidden=true`.
- Tabelas possuem `aria-sort`; linhas navegáveis usam links reais quando possível.
- Toasts, mudanças de frescor e validação usam live region adequada.
- `lang="pt-BR"`; aspas curvas; loading termina em `…`.
- `—` significa apenas dado ausente.

## 17. Mockups aprovados

| Ordem | Arquivo | Papel |
|---:|---|---|
| 1 | `mockups/current/01-login-imersivo.png` | Login e torus como substituto do visual provisório |
| 2 | `mockups/current/02-home-abertura-narrativa.png` | Home narrativa |
| 3 | `mockups/current/03-home-mudancas-mercado.png` | Home analítica |
| 4 | `mockups/current/04-previsoes-resumo-horizontes.png` | resumo e horizontes |
| 5 | `mockups/current/05-previsoes-tabela-cenarios.png` | tabela de previsões |
| 6 | `mockups/current/06-previsoes-monte-carlo.png` | Monte Carlo |

O Login aprovado usa provisoriamente uma esfera na imagem; a implementação final substitui esse elemento pelo **torus** definido na seção 8.2, preservando posição, escala, contraste e formulário.

## 18. Critérios de aceite para implementação

A implementação visual só está concluída quando:

- a marca aparece como **CRYPTO FORECASTING** em todos os locais;
- Geist/Geist Mono substituem as fontes anteriores;
- Home e Previsões seguem a ordem narrativa → dados;
- Leitura do Dia e Resumo da Rodada não têm card;
- tabelas e Monte Carlo não têm container externo emoldurado;
- fundos apresentam gradiente mineral e microgrão sem comprometer contraste;
- o Login usa o torus ou poster aprovado e possui fallback de redução de movimento;
- Monte Carlo desenha progressivamente e destaca verde/ciano/vermelho ao final;
- snapshot, warm-up, stale, erros e sessão expirada seguem as regras deste documento;
- desktop, tablet, mobile, teclado e redução de movimento foram verificados;
- nenhuma regra de UI/UX depende de documento removido ou mockup legado.
