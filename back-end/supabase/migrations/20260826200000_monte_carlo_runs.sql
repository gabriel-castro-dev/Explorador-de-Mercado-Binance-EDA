-- ML iteração 2 (Monte Carlo fase 1): trajetórias simuladas pelo job ml-forecast.
-- Uma linha por (símbolo, model_version): n_simulated trajetórias em PREÇO, com
-- horizon_days passos de step_seconds cada, e a classificação best/base/worst
-- (índices em paths). Trajetórias são dados, não artefatos (ADR-0004).
-- Padrão de acesso do projeto: RLS + authenticated_select; escrita só service_role.

create table public.monte_carlo_runs (
    id            bigint generated always as identity primary key,
    symbol        text not null references public.symbols (symbol),
    model_version text not null,
    run_at        timestamptz not null,
    horizon_days  smallint not null check (horizon_days between 1 and 30),
    step_seconds  integer not null check (step_seconds > 0),
    n_simulated   integer not null check (n_simulated > 0),
    -- ~1000 × 7 números (≈80 KB) por linha: cabe em jsonb; se pesar, Storage + ponteiro.
    paths         jsonb not null,
    classified    jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now(),
    -- Upsert idempotente do job diário.
    unique (symbol, model_version)
);

-- Leitura da API: "nuvem mais recente de um símbolo". O índice também cobre a FK.
create index monte_carlo_runs_symbol_run_at_idx on public.monte_carlo_runs (symbol, run_at desc);

alter table public.monte_carlo_runs enable row level security;
create policy "authenticated_select" on public.monte_carlo_runs
    for select to authenticated using (true);
