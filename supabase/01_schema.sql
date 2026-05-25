-- =============================================================================
-- Monitor Electoral de Escucha Digital — Esquema para Supabase (PASO 1 de 3)
-- -----------------------------------------------------------------------------
-- Pega TODO este script en:  Supabase  ->  SQL Editor  ->  New query  ->  Run
-- Crea las tablas, la seguridad (RLS) y el contexto electoral configurable.
-- Luego ejecuta 02_functions.sql y 03_seed_demo.sql.
-- =============================================================================

-- --- Tablas de contexto (editables para adaptar a cualquier elección) --------

create table if not exists project_info (
  id        int primary key default 1,
  name      text not null default 'Monitor Electoral',
  language  text not null default 'es',
  country   text not null default 'GENERICO',
  election  text not null default 'Elecciones Generales',
  timezone  text not null default 'America/Bogota',
  constraint project_info_single_row check (id = 1)
);

create table if not exists topics (
  id       text primary key,
  name     text not null,
  keywords text[] not null default '{}',   -- para clasificar menciones por tema
  sort     int  default 0
);

create table if not exists actors (
  id       text primary key,
  name     text not null,
  party    text,
  color    text not null default '#64748b',
  aliases  text[] not null default '{}',    -- variantes de texto / @usuarios
  sort     int  default 0
);

-- Compatibilidad si las tablas ya existían de una ejecución anterior:
alter table topics add column if not exists keywords text[] not null default '{}';
alter table actors add column if not exists aliases  text[] not null default '{}';

create table if not exists sources (
  id       text primary key,
  label    text not null,
  enabled  boolean not null default true,
  config   jsonb   not null default '{}',  -- feeds / subreddits / query_terms para la ingesta
  sort     int  default 0
);

alter table sources add column if not exists config jsonb not null default '{}';

-- --- Tabla principal: menciones ----------------------------------------------

create table if not exists mentions (
  id              bigint generated always as identity primary key,
  source          text not null,
  external_id     text unique,
  author          text,
  text            text not null,
  url             text,
  lang            text not null default 'es',
  published_at    timestamptz not null,
  engagement      int    not null default 0,
  reach           bigint not null default 0,
  sentiment       text   not null default 'neutral',
  sentiment_score real   not null default 0,
  emotion         text,
  topic           text,
  actors          text[] not null default '{}',
  created_at      timestamptz not null default now()
);

create index if not exists ix_mentions_published on mentions (published_at);
create index if not exists ix_mentions_source    on mentions (source);
create index if not exists ix_mentions_topic     on mentions (topic);
create index if not exists ix_mentions_sentiment on mentions (sentiment);
create index if not exists ix_mentions_actors    on mentions using gin (actors);

-- --- Seguridad (RLS): lectura pública para el dashboard ----------------------
-- El dashboard usa la "anon key" (pública) y solo necesita LEER.
-- Las escrituras (sembrar/ingerir) se hacen desde el SQL Editor (rol postgres),
-- que omite RLS. Si tus datos fueran sensibles, restringe estas políticas.

alter table project_info enable row level security;
alter table topics       enable row level security;
alter table actors       enable row level security;
alter table sources      enable row level security;
alter table mentions     enable row level security;

drop policy if exists public_read_project on project_info;
drop policy if exists public_read_topics  on topics;
drop policy if exists public_read_actors  on actors;
drop policy if exists public_read_sources on sources;
drop policy if exists public_read_mentions on mentions;

create policy public_read_project  on project_info for select using (true);
create policy public_read_topics   on topics       for select using (true);
create policy public_read_actors   on actors       for select using (true);
create policy public_read_sources  on sources      for select using (true);
create policy public_read_mentions on mentions      for select using (true);

grant usage on schema public to anon, authenticated;
grant select on project_info, topics, actors, sources, mentions to anon, authenticated;

-- --- Datos de contexto (equivalente a config/election.yaml) ------------------

insert into project_info (id, name, language, country, election, timezone)
values (1, 'Monitor Electoral', 'es', 'GENERICO', 'Elecciones Generales', 'America/Bogota')
on conflict (id) do update set
  name = excluded.name, language = excluded.language, country = excluded.country,
  election = excluded.election, timezone = excluded.timezone;

insert into topics (id, name, keywords, sort) values
  ('economia', 'Economía y empleo',
    array['economia','economía','inflacion','inflación','empleo','desempleo','impuestos','salario','trabajo','costo de vida','precios'], 1),
  ('seguridad', 'Seguridad',
    array['seguridad','crimen','delincuencia','violencia','policia','policía','narcotrafico','narcotráfico','homicidios','robo'], 2),
  ('salud', 'Salud',
    array['salud','hospital','hospitales','eps','medicina','medicamentos','sistema de salud','pandemia'], 3),
  ('educacion', 'Educación',
    array['educacion','educación','colegios','universidad','universidades','docentes','profesores','estudiantes','matricula'], 4),
  ('corrupcion', 'Corrupción y transparencia',
    array['corrupcion','corrupción','transparencia','soborno','coima','escandalo','escándalo','robo de recursos','clientelismo'], 5),
  ('medio_ambiente', 'Medio ambiente',
    array['ambiente','medioambiente','clima','deforestacion','deforestación','agua','contaminacion','contaminación','energia','energía'], 6),
  ('migracion', 'Migración',
    array['migracion','migración','migrantes','frontera','refugiados','venezolanos','xenofobia'], 7),
  ('infraestructura', 'Infraestructura y servicios',
    array['infraestructura','vias','vías','transporte','movilidad','obras','servicios publicos','servicios públicos','agua potable','energia electrica'], 8)
on conflict (id) do update set name = excluded.name, keywords = excluded.keywords, sort = excluded.sort;

insert into actors (id, name, party, color, aliases, sort) values
  ('candidato_a', 'Candidato A',  'Partido Azul',    '#2563eb', array['Candidato A','Cand A','@candidatoA','el candidato azul'], 1),
  ('candidato_b', 'Candidata B',  'Partido Verde',   '#16a34a', array['Candidata B','Cand B','@candidataB','la candidata verde'], 2),
  ('candidato_c', 'Candidato C',  'Partido Naranja', '#ea580c', array['Candidato C','Cand C','@candidatoC','el naranja'], 3),
  ('candidato_d', 'Candidata D',  'Partido Morado',  '#9333ea', array['Candidata D','Cand D','@candidataD'], 4)
on conflict (id) do update set
  name = excluded.name, party = excluded.party, color = excluded.color, aliases = excluded.aliases, sort = excluded.sort;

insert into sources (id, label, enabled, config, sort) values
  ('twitter',   'X / Twitter',    true,  '{"query_terms":["elecciones","voto","campaña"]}'::jsonb, 1),
  ('news',      'Noticias / RSS', true,  '{"feeds":["https://feeds.bbci.co.uk/mundo/rss.xml","https://www.eltiempo.com/rss/colombia.xml"]}'::jsonb, 2),
  ('reddit',    'Reddit / Foros', true,  '{"subreddits":["politica","colombia","mexico"]}'::jsonb, 3),
  ('youtube',   'YouTube',        false, '{"query_terms":["elecciones","debate presidencial"]}'::jsonb, 4),
  ('tiktok',    'TikTok',         false, '{}'::jsonb, 5),
  ('instagram', 'Instagram',      false, '{}'::jsonb, 6)
on conflict (id) do update set label = excluded.label, sort = excluded.sort, config = excluded.config;
