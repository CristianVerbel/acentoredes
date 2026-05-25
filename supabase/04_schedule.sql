-- =============================================================================
-- Monitor Electoral — Programar la ingesta automática (OPCIONAL)
-- -----------------------------------------------------------------------------
-- Hace que la Edge Function "ingest" se ejecute periódicamente (p. ej. cada
-- hora) para traer menciones nuevas. Todo desde el SQL Editor de Supabase.
--
-- ALTERNATIVA SIN SQL: Supabase -> Edge Functions -> (tu función) -> pestaña
-- "Schedules" / "Cron", y define el intervalo desde la interfaz web.
-- =============================================================================

-- 1) Habilita las extensiones (una sola vez)
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- 2) Programa la llamada. EDITA los valores en MAYÚSCULAS:
--    - PROYECTO            : la referencia de tu proyecto (xxxx en xxxx.supabase.co)
--    - SERVICE_ROLE_KEY    : Project Settings -> API -> service_role (secreta)
--    - INGEST_SECRET       : el mismo valor del secret INGEST_SECRET (si lo usas)
--    El cron '0 * * * *' = cada hora en punto. Cambia a gusto.
--
--    (Re-ejecutar este bloque actualiza el job gracias al unschedule previo.)

select cron.unschedule('monitor-ingest') where exists (
  select 1 from cron.job where jobname = 'monitor-ingest'
);

select cron.schedule(
  'monitor-ingest',
  '0 * * * *',
  $$
  select net.http_post(
    url     := 'https://PROYECTO.functions.supabase.co/ingest?limit=50',
    headers := jsonb_build_object(
      'Content-Type',  'application/json',
      'Authorization', 'Bearer SERVICE_ROLE_KEY',
      'x-ingest-key',  'INGEST_SECRET'
    )
  );
  $$
);

-- 3) Ver / quitar el job
-- select jobid, jobname, schedule, active from cron.job;
-- select cron.unschedule('monitor-ingest');
