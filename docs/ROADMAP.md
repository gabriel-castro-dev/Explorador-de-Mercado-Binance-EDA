# Roadmap — próximos marcos

Quatro marcos **independentes** (qualquer ordem). Cada um será detalhado em plan mode na sua hora — isto é o overview do que o agente deve buscar: segurança, stack clara, arquitetura limpa. Antes de cada marco: ler `AGENTS.md` e as convenções em `docs/agents/`.

## 1. Front-end (dashboard)

**Stack decidida:** Vue 3 + Nuxt + Tailwind CSS, em `front-end/` na raiz do monorepo. Auth via `supabase-js` direto no Supabase Auth (login, signup, reset de senha, refresh de sessão); a API é consumida com o access token em `Authorization: Bearer`.

**Escopo:** telas de login/cadastro; dashboard com seletor de ativos (`/symbols`), gráfico de candles (`/klines`), overlay de indicadores (`/features`), tabela-resumo 24h (`/tickers/24h`).

**Atenção:** só a **publishable key** no client (nunca service_role/secret); CORS da API alinhado ao domínio final (`API_CORS_ORIGINS`); tokens nunca em localStorage manual (deixar o supabase-js gerenciar); estados de 401 → redirect para login. Skills úteis: `frontend-design`, `dataviz` (gráficos), `composition-patterns`.

## 2. UX & Usabilidade

**Escopo:** passada de UX sobre o front — onboarding, estados de loading/vazio/erro em todas as telas, responsividade mobile, acessibilidade (contraste, navegação por teclado, labels), feedbacks claros de auth (sem vazar se o e-mail existe), dark mode.

**Atenção:** mensagens de erro genéricas em falha de login (segurança); warm-up de indicadores (`null`s) precisa de tratamento visual, não tela quebrada; latência da API → skeletons. Skills úteis: `web-design-guidelines` (auditoria), `frontend-design`.

## 3. ML / Forecasting

**Escopo:** treino agendado (GitHub Actions, imagem própria como os jobs); modelos baseline primeiro (ex.: Prophet / sklearn) sobre as tabelas `features_*`; novas tabelas `predictions` e `model_metrics` (versão do modelo, MAE/RMSE por rodada); endpoint `GET /api/v1/forecasts` na API existente.

**Atenção:** **split temporal** no treino/validação (nunca aleatório — data leakage em séries temporais); RLS nas tabelas novas (o event trigger já liga RLS automaticamente, mas a policy `authenticated_select` precisa ser criada explicitamente); migrations versionadas em `back-end/supabase/migrations/`; escrita só via service_role dos jobs; rastreabilidade modelo→métrica→previsão.

## 4. Deploy em nuvem

**Escopo:** VM (Hostinger) com docker compose puxando `ghcr.io/.../crypto-api` (PAT `read:packages` — o GITHUB_TOKEN não funciona fora do run); reverse proxy (Caddy ou nginx) com **HTTPS obrigatório**; workflow `deploy-api.yml` via SSH (desenho já documentado no histórico de planos); front na Vercel ou no domínio grátis da VM (decisão pendente). 

**Atenção:** secrets só em env na VM (nunca no git); firewall liberando só 80/443/SSH; `SUPABASE_KEY` service_role **não** vai para o container da API (só `SUPABASE_PUBLISHABLE_KEY`); monitoramento via `/health`; **backups do banco** (free tier do Supabase não tem backup automático — agendar `pg_dump` ou upgrade); rotação da chave SSH do deploy.
