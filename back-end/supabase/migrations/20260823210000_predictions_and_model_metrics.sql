-- Marco 3 (ML/Forecasting): tabelas de previsões e métricas por rodada.
-- Padrão de acesso do projeto (migrations de 2026-08-19):
--   * o event trigger ensure_rls liga RLS em toda tabela nova (deny até haver policy);
--   * default privileges já dão SELECT a authenticated em tabelas novas — falta a policy;
--   * escrita fica só com o service_role dos jobs (ignora RLS; sem policies de escrita).

-- 1. predictions: uma linha por (símbolo, data-alvo, horizonte, versão do modelo).
create table public.predictions (
    id                   bigint generated always as identity primary key,
    symbol               text not null references public.symbols (symbol),
    model_version        text not null,
    run_at               timestamptz not null,
    target_time          timestamptz not null,
    horizon_days         smallint not null check (horizon_days between 1 and 30),
    predicted_close      double precision not null check (predicted_close > 0),
    predicted_log_return double precision not null,
    pred_lower           double precision not null check (pred_lower > 0),
    pred_upper           double precision not null check (pred_upper > 0),
    is_fallback          boolean not null default false,
    created_at           timestamptz not null default now(),
    -- Upsert idempotente do job diário.
    unique (symbol, target_time, horizon_days, model_version)
);

-- Leitura da API: "previsões do run mais recente (por símbolo)".
create index predictions_run_at_idx on public.predictions (run_at desc);
create index predictions_symbol_run_at_idx on public.predictions (symbol, run_at desc);

-- 2. model_metrics: rastreabilidade modelo → métrica → previsão (via model_version).
create table public.model_metrics (
    id               bigint generated always as identity primary key,
    model_version    text not null unique,
    model_type       text not null,
    trained_at       timestamptz not null,
    train_start      timestamptz not null,
    train_end        timestamptz not null,
    git_sha          text,
    hyperparams      jsonb not null default '{}'::jsonb,
    metrics          jsonb not null default '{}'::jsonb,
    baseline_mae     jsonb not null default '{}'::jsonb,
    realized_metrics jsonb,
    is_fallback      boolean not null default false,
    created_at       timestamptz not null default now()
);

-- 3. RLS: explícito e idempotente (não depender só do event trigger) + policy de leitura.
alter table public.predictions   enable row level security;
alter table public.model_metrics enable row level security;

create policy "authenticated_select" on public.predictions   for select to authenticated using (true);
create policy "authenticated_select" on public.model_metrics for select to authenticated using (true);
