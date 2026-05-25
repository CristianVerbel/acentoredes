-- =============================================================================
-- Monitor Electoral — Funciones de analítica (RPC) para Supabase (PASO 2 de 3)
-- -----------------------------------------------------------------------------
-- Pega TODO este script en el SQL Editor de Supabase y ejecútalo.
-- Define las funciones que el dashboard consume vía supabase.rpc(...).
-- Todas aceptan los mismos filtros opcionales:
--   p_from, p_to (ISO date/timestamp), p_source, p_actor, p_topic,
--   p_sentiment, p_q (búsqueda de texto).
-- =============================================================================

-- --- Configuración (actores, temáticas, fuentes) para el frontend ------------
create or replace function get_config()
returns jsonb language sql stable as $$
  select jsonb_build_object(
    'project', (select to_jsonb(p) from project_info p where id = 1),
    'actors', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', id, 'name', name, 'type', 'candidate',
        'party', party, 'color', color, 'aliases', to_jsonb(aliases)
      ) order by sort) from actors
    ), '[]'::jsonb),
    'topics', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', id, 'name', name, 'keywords', to_jsonb(keywords)
      ) order by sort) from topics
    ), '[]'::jsonb),
    'sources', coalesce((
      select jsonb_object_agg(id, jsonb_build_object(
        'label', label, 'enabled', enabled, 'available', false
      )) from sources
    ), '{}'::jsonb),
    'llm_analysis', false
  );
$$;

-- --- KPIs / resumen ----------------------------------------------------------
create or replace function get_summary(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), agg as (
    select
      count(*) total,
      coalesce(sum(reach), 0) reach,
      coalesce(sum(engagement), 0) eng,
      count(*) filter (where sentiment = 'positive') pos,
      count(*) filter (where sentiment = 'neutral')  neu,
      count(*) filter (where sentiment = 'negative') neg,
      coalesce(avg(sentiment_score), 0) avgs,
      count(distinct author) authors,
      count(distinct source) srcs,
      min(published_at) pmin,
      max(published_at) pmax
    from f
  )
  select jsonb_build_object(
    'total_mentions', total,
    'total_reach', reach,
    'total_engagement', eng,
    'sentiment', jsonb_build_object('positive', pos, 'neutral', neu, 'negative', neg),
    'avg_sentiment_score', round(avgs::numeric, 4),
    'net_sentiment', case when total = 0 then 0 else round((pos - neg)::numeric / total * 100, 1) end,
    'unique_authors', authors,
    'sources_count', srcs,
    'top_topic', (select topic from f where topic is not null group by topic order by count(*) desc limit 1),
    'period_start', pmin,
    'period_end', pmax
  ) from agg;
$$;

-- --- Evolución temporal (por día) --------------------------------------------
create or replace function get_timeline(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), days as (
    select to_char(published_at, 'YYYY-MM-DD') d,
      count(*) total,
      count(*) filter (where sentiment = 'positive') pos,
      count(*) filter (where sentiment = 'neutral')  neu,
      count(*) filter (where sentiment = 'negative') neg
    from f group by 1
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'date', d, 'total', total, 'positive', pos, 'neutral', neu, 'negative', neg,
    'net_sentiment', case when total = 0 then 0 else round((pos - neg)::numeric / total * 100, 1) end
  ) order by d), '[]'::jsonb) from days;
$$;

-- --- Temáticas ----------------------------------------------------------------
create or replace function get_topics(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), t as (
    select topic id, count(*) cnt,
      count(*) filter (where sentiment = 'positive') pos,
      count(*) filter (where sentiment = 'neutral')  neu,
      count(*) filter (where sentiment = 'negative') neg,
      coalesce(avg(sentiment_score), 0) avgs
    from f where topic is not null group by topic
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'id', t.id, 'name', coalesce(tp.name, t.id), 'count', cnt,
    'positive', pos, 'neutral', neu, 'negative', neg,
    'net_sentiment', case when cnt = 0 then 0 else round((pos - neg)::numeric / cnt * 100, 1) end,
    'avg_score', round(avgs::numeric, 4)
  ) order by cnt desc), '[]'::jsonb)
  from t left join topics tp on tp.id = t.id;
$$;

-- --- Fuentes ------------------------------------------------------------------
create or replace function get_sources(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), s as (
    select source, count(*) cnt,
      count(*) filter (where sentiment = 'positive') pos,
      count(*) filter (where sentiment = 'neutral')  neu,
      count(*) filter (where sentiment = 'negative') neg
    from f group by source
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'source', s.source, 'label', coalesce(src.label, s.source), 'count', cnt,
    'positive', pos, 'neutral', neu, 'negative', neg,
    'net_sentiment', case when cnt = 0 then 0 else round((pos - neg)::numeric / cnt * 100, 1) end
  ) order by cnt desc), '[]'::jsonb)
  from s left join sources src on src.id = s.source;
$$;

-- --- Share of voice por actor -------------------------------------------------
create or replace function get_share_of_voice(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), exploded as (
    select unnest(actors) actor_id, sentiment, reach from f
  ), total as (
    select count(*) c from exploded
  ), a as (
    select actor_id, count(*) cnt,
      count(*) filter (where sentiment = 'positive') pos,
      count(*) filter (where sentiment = 'neutral')  neu,
      count(*) filter (where sentiment = 'negative') neg,
      coalesce(sum(reach), 0) rch
    from exploded group by actor_id
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'actor_id', ac.id, 'name', ac.name, 'party', ac.party, 'color', ac.color,
    'count', coalesce(a.cnt, 0),
    'share', case when (select c from total) = 0 then 0
                  else round(coalesce(a.cnt, 0)::numeric / (select c from total) * 100, 1) end,
    'positive', coalesce(a.pos, 0), 'neutral', coalesce(a.neu, 0), 'negative', coalesce(a.neg, 0),
    'net_sentiment', case when coalesce(a.cnt, 0) = 0 then 0
                          else round((coalesce(a.pos, 0) - coalesce(a.neg, 0))::numeric / a.cnt * 100, 1) end,
    'total_reach', coalesce(a.rch, 0)
  ) order by coalesce(a.cnt, 0) desc), '[]'::jsonb)
  from actors ac left join a on a.actor_id = ac.id;
$$;

-- --- Emociones ----------------------------------------------------------------
create or replace function get_emotions(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), e as (
    select emotion, count(*) cnt from f where emotion is not null group by emotion
  )
  select coalesce(jsonb_agg(jsonb_build_object('emotion', emotion, 'count', cnt) order by cnt desc), '[]'::jsonb)
  from e;
$$;

-- --- Feed de menciones (paginado) --------------------------------------------
create or replace function get_mentions(
  p_from timestamptz default null, p_to timestamptz default null,
  p_source text default null, p_actor text default null, p_topic text default null,
  p_sentiment text default null, p_q text default null,
  p_limit int default 40, p_offset int default 0, p_sort text default 'recent'
) returns jsonb language sql stable as $$
  with f as (
    select * from mentions m
    where (p_from is null or m.published_at >= p_from)
      and (p_to is null or m.published_at <= p_to)
      and (p_source is null or m.source = p_source)
      and (p_topic is null or m.topic = p_topic)
      and (p_sentiment is null or m.sentiment = p_sentiment)
      and (p_actor is null or p_actor = any(m.actors))
      and (p_q is null or m.text ilike '%' || p_q || '%')
  ), ord as (
    select f.*, row_number() over (
      order by (case when p_sort = 'engagement' then engagement::numeric
                     when p_sort = 'reach' then reach::numeric
                     else extract(epoch from published_at)::numeric end) desc
    ) rn
    from f
  )
  select jsonb_build_object(
    'total', (select count(*) from f),
    'limit', p_limit,
    'offset', p_offset,
    'items', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', id, 'source', source, 'author', author, 'text', text, 'url', url, 'lang', lang,
        'published_at', published_at, 'engagement', engagement, 'reach', reach,
        'sentiment', sentiment, 'sentiment_score', sentiment_score, 'emotion', emotion,
        'topic', topic, 'actors', to_jsonb(actors)
      ) order by rn)
      from ord where rn > p_offset and rn <= p_offset + p_limit
    ), '[]'::jsonb)
  );
$$;

-- --- Permisos de ejecución para el dashboard (anon key) ----------------------
grant execute on function
  get_config(),
  get_summary(timestamptz, timestamptz, text, text, text, text, text),
  get_timeline(timestamptz, timestamptz, text, text, text, text, text),
  get_topics(timestamptz, timestamptz, text, text, text, text, text),
  get_sources(timestamptz, timestamptz, text, text, text, text, text),
  get_share_of_voice(timestamptz, timestamptz, text, text, text, text, text),
  get_emotions(timestamptz, timestamptz, text, text, text, text, text),
  get_mentions(timestamptz, timestamptz, text, text, text, text, text, int, int, text)
to anon, authenticated;
