-- Aplicada em produção via MCP em 2026-08-26.
-- Duas views de leitura para a API; nenhuma tabela nova, nenhuma escrita.
--
-- 1. symbols_with_tracking — a tabela symbols acumula todo par visto pelo job
--    de tickers (735), mas só o universo de análise (~20) tem candles. `tracked`
--    é derivado dos dados (existe linha em klines_1d), nunca digitado à mão: se
--    um ativo sair do universo, deixa de ser rastreado sozinho.
-- 2. ticker_24hr_latest — snapshot 24h mais recente por símbolo. Substitui a
--    heurística "200 linhas mais novas" do repositório, que deixava BTC/ETH/BNB
--    de fora quando o job grava 480–735 símbolos por lote.
--    Forma LATERAL (1 busca no índice por símbolo, ~25 ms) em vez de
--    DISTINCT ON, que varria as ~75k linhas da tabela (~1,5 s medido).
--    Todo símbolo de ticker_24hr_history existe em symbols (FK), então nada
--    fica de fora.
--
-- Segurança (padrão das migrations de 2026-08-19): security_invoker = true faz a
-- view rodar com o papel do chamador, então as policies authenticated_select das
-- tabelas base continuam valendo e anon segue negado. Grants explícitos: SELECT
-- só para authenticated e service_role.
--
-- Índices: klines_1d (symbol, open_time) cobre o EXISTS; ticker_24hr_history
-- (symbol, open_time) unique cobre o ORDER BY ... LIMIT 1 por símbolo (scan
-- reverso) — nenhum índice novo.

create or replace view public.symbols_with_tracking
with (security_invoker = true) as
select
    s.symbol,
    s.created_at,
    exists (
        select 1
        from public.klines_1d k
        where k.symbol = s.symbol
    ) as tracked
from public.symbols s;

comment on view public.symbols_with_tracking is
    'symbols + tracked (tem candles em klines_1d). Fonte de GET /api/v1/symbols.';

create or replace view public.ticker_24hr_latest
with (security_invoker = true) as
select
    l.*,
    exists (
        select 1
        from public.klines_1d k
        where k.symbol = s.symbol
    ) as tracked
from public.symbols s
cross join lateral (
    select t.*
    from public.ticker_24hr_history t
    where t.symbol = s.symbol
    order by t.open_time desc
    limit 1
) l;

comment on view public.ticker_24hr_latest is
    'Linha mais recente de ticker_24hr_history por símbolo. Fonte de GET /api/v1/tickers/24h.';

revoke all on public.symbols_with_tracking, public.ticker_24hr_latest from public, anon;
grant select on public.symbols_with_tracking, public.ticker_24hr_latest to authenticated, service_role;
