-- Aplicada em produção via MCP em 2026-08-19 (Fase 6 do refactor pré-API).
-- Grants de tabela: RLS só filtra linhas; o privilégio SELECT é pré-requisito.
-- anon: nada. authenticated: só SELECT. TRUNCATE/REFERENCES/TRIGGER/MAINTAIN ignoram RLS → revogar.

revoke all on all tables in schema public from anon, authenticated;
grant select on all tables in schema public to authenticated;

-- Tabelas futuras (owner postgres, schema public): mesmo padrão.
-- Com o event trigger ensure_rls (RLS automático do Supabase), toda tabela nova nasce com RLS on
-- e sem policy (deny); o SELECT default para authenticated só vale após uma policy explícita.
alter default privileges for role postgres in schema public revoke all on tables from anon, authenticated;
alter default privileges for role postgres in schema public grant select on tables to authenticated;
