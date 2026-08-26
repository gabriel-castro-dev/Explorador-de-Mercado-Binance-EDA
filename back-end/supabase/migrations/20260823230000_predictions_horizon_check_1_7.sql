-- Alinha o contrato do banco ao vocabulário (CONTEXT.md): horizonte é 1–7 dias.
-- A migration 20260823210000 nasceu com 1–30 por folga; sem uso, a folga só
-- enfraquece o contrato.
alter table public.predictions drop constraint if exists predictions_horizon_days_check;
alter table public.predictions
    add constraint predictions_horizon_days_check check (horizon_days between 1 and 7);
