-- Aplicada em produção via MCP em 2026-08-19 (Fase 6 do refactor pré-API).
-- RLS: SELECT para authenticated em todas as tabelas, deny para anon.
-- Escrita fica só para service_role (jobs), que ignora RLS.

-- 1. Garantir RLS habilitado (idempotente)
alter table public.symbols             enable row level security;
alter table public.klines_15m          enable row level security;
alter table public.klines_1h           enable row level security;
alter table public.klines_1d           enable row level security;
alter table public.ticker_24hr_history enable row level security;
alter table public.orderbook_tickers   enable row level security;
alter table public.features_15m        enable row level security;
alter table public.features_1h         enable row level security;
alter table public.features_24h        enable row level security;

-- 2. Remover leitura pública (anon)
drop policy if exists "Leitura pública de klines_15m"  on public.klines_15m;
drop policy if exists "Leitura pública de klines_1h"   on public.klines_1h;
drop policy if exists "Leitura pública de klines_1d"   on public.klines_1d;
drop policy if exists "Leitura pública de orderbook"   on public.orderbook_tickers;
drop policy if exists "Leitura pública de symbols"     on public.symbols;
drop policy if exists "Leitura pública de ticker_24hr" on public.ticker_24hr_history;

-- 3. SELECT para usuários autenticados
create policy "authenticated_select" on public.symbols             for select to authenticated using (true);
create policy "authenticated_select" on public.klines_15m          for select to authenticated using (true);
create policy "authenticated_select" on public.klines_1h           for select to authenticated using (true);
create policy "authenticated_select" on public.klines_1d           for select to authenticated using (true);
create policy "authenticated_select" on public.ticker_24hr_history for select to authenticated using (true);
create policy "authenticated_select" on public.orderbook_tickers   for select to authenticated using (true);
create policy "authenticated_select" on public.features_15m        for select to authenticated using (true);
create policy "authenticated_select" on public.features_1h         for select to authenticated using (true);
create policy "authenticated_select" on public.features_24h        for select to authenticated using (true);

-- 4. clean_old_data: SECURITY DEFINER exposto via RPC a anon/authenticated = delete arbitrário.
--    Só os jobs (service_role) podem chamar. search_path fixo (lint 0011).
revoke execute on function public.clean_old_data(text, text, text) from public, anon, authenticated;
grant  execute on function public.clean_old_data(text, text, text) to service_role;
alter function public.clean_old_data(text, text, text) set search_path = '';

-- 5. Demais funções: fechar RPC e fixar search_path
revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
alter function public.auto_insert_missing_symbol() set search_path = '';

-- 6. Índice/constraint duplicado em orderbook_tickers (advisor de performance)
alter table public.orderbook_tickers drop constraint if exists orderbook_tickers_symbol_fetched_at_key;
