# Design do dashboard — índice

Entrega de **design** do produto (v2 · Dark-Tech). A implementação segue `docs/plans/2026-08-19-front-end-architecture.md` (arquitetura) + [Design.md](Design.md) (visual).

| Artefato | Onde |
|---|---|
| **Canvas de mockups v2** (19 artboards: login split, auth, Início/insights, Gráficos + cenários IA, Previsões, Mercado, Preferências, estados, design system, componentes — desktop e mobile) | https://claude.ai/code/artifact/d3e48655-f0d1-4113-b161-100ef74d5cd8 (versão `v2-dark-tech`; a v1 "Observatório" está no histórico de versões) |
| **Design system (documento oficial)** | [Design.md](Design.md) — cores HEX, Google Sans, vidro, regras para devs, telas |
| Fonte dos mockups | [canvas/build.mjs](canvas/build.mjs) (v2) · [canvas/v1/build.v1.mjs](canvas/v1/build.v1.mjs) (v1) — `node build.mjs` regenera os `.dc.html` + `canvas.json` (gerados; `*.json` é git-ignored) |
| Capturas | [mockups/](mockups/) — login, home (+mobile), gráficos, previsões, preferências, mercado, estados, design-system |
| Especificação de UX (fluxos de auth com mensagens exatas, estados, frescor, responsivo, a11y, microcopy) | [ux-spec.md](ux-spec.md) — segue válida; onde divergir da v2, o Design.md vence |
| Inventário de componentes → Nuxt UI (v1 + novos da v2 no artboard "Componentes") | [components.md](components.md) |
| Auditorias (Web Interface Guidelines + validação de paleta v1 e v2) | [audit.md](audit.md) |

## Direção v2 em 6 linhas

1. **Dark-Tech**: navy quase preto `#060b16`, cards de vidro (blur 14, borda branco-gelo 14 %), luz azul elétrica `#3e86f7` usada com moderação (≤ 20 %).
2. **Ciano `#5fc4ff` (derivado do glow da logo) = IA**: previsões, gaps, resumos do modelo — só isso.
3. **Velas**: alta **vazada em vidro-gelo** (como na logo), baixa vermelha `#e5484d`. Sem verde, roxo, rosa ou laranja em lugar nenhum.
4. **Google Sans** (UI) + **Google Sans Code** (números tabulares, UTC, símbolos).
5. **Fluxo**: Login split (bullets do conceito + créditos/GitHub/LinkedIn) → **Início** com "as principais mudanças desde o seu último acesso" (top-5 volatilidade / gap IA / volume) → Gráficos (candles + cenários melhor/esperado/pior) → Previsões (tabela de horizontes + resumo em texto + Monte Carlo "em breve") → Mercado → Preferências (dados, telefone, notificações, SMS/WhatsApp "em breve").
6. **Honestidade mantida da v1**: selo de snapshot, linha de corte, estados de warm-up/vazio/erro, mensagens de auth genéricas; dados de IA levam chip "IA · v0 · em validação" até o marco 3.

## Decisões com o usuário

| Data | Decisão |
|---|---|
| 2026-08-19 | densidade média · tabela 24h em rota própria · (v1) analítico sóbrio dark+light |
| 2026-08-22 | **redesign Dark-Tech** · dark-only · alta = vidro-gelo vazado · telas de IA no estado final com selo "em validação" |

Referência IAagro citada no brief não foi anexada — o login seguiu a descrição (painel esquerdo institucional + formulário à direita); ajustável quando a imagem chegar.
