-- =============================================================================
-- Monitor Electoral — Datos demo (PASO 3 de 3) para Supabase
-- -----------------------------------------------------------------------------
-- Pega TODO este script en el SQL Editor de Supabase y ejecútalo.
-- Crea la función seed_demo_data() y la ejecuta para llenar el dashboard con
-- menciones simuladas (no son datos reales; solo para visualizar el monitor).
--
-- Para re-sembrar más tarde:   select seed_demo_data(75, 60);
-- =============================================================================

create or replace function seed_demo_data(p_days int default 75, p_per_day int default 60)
returns int
language plpgsql
as $$
declare
  v_total int := 0;
  d int; i int; v_count int;
  v_source text; v_topic_id text; v_topic_name text;
  v_actor_id text; v_actor_name text; v_actor_idx int;
  v_sentiment text; v_emotion text; v_text text;
  v_eng int; v_reach bigint; v_pub timestamptz;
  v_r real; v_cum real; j int;

  topic_ids   text[]; topic_names text[];
  actor_ids   text[]; actor_names text[];

  -- Fuentes y sus pesos / rangos de engagement
  src_ids   text[] := array['twitter','news','reddit','youtube','tiktok','instagram'];
  src_w     real[] := array[0.42, 0.12, 0.18, 0.12, 0.10, 0.06];
  src_emin  int[]  := array[5, 0, 2, 10, 50, 20];
  src_emax  int[]  := array[800, 50, 400, 2000, 5000, 3000];

  -- Sesgo de sentimiento por actor (pos, neu, neg) según su índice
  lean_pos real[] := array[0.45, 0.30, 0.38, 0.25];
  lean_neu real[] := array[0.30, 0.30, 0.34, 0.35];
  -- Peso de share of voice por actor
  sov_w    real[] := array[0.36, 0.30, 0.22, 0.12];

  tpl_pos text[] := array[
    'Me convence la propuesta de %1$s sobre %2$s. Por fin alguien con un plan serio.',
    'Gran intervención de %1$s en el debate, sobre todo en %2$s. #Elecciones',
    '%1$s demuestra liderazgo en %2$s. Tiene mi voto.',
    'Excelente lo que plantea %1$s para %2$s, ojalá se cumpla.',
    'Confío en %1$s, su discurso sobre %2$s fue claro y con propuestas.'
  ];
  tpl_neg text[] := array[
    'Otra vez %1$s con promesas vacías sobre %2$s. Pura demagogia.',
    'Es una vergüenza lo que dijo %1$s acerca de %2$s. No le creo nada.',
    '%1$s no tiene ni idea de %2$s, sus propuestas son un desastre.',
    'La corrupción de siempre con %1$s. El tema de %2$s le queda grande.',
    'Decepcionante %1$s, en %2$s solo repite mentiras. #Fraude'
  ];
  tpl_neu text[] := array[
    '%1$s presentó hoy su plan sobre %2$s. Habrá que ver los detalles.',
    'En el foro se discutió la postura de %1$s frente a %2$s.',
    'Nota: %1$s habló de %2$s en la entrevista de esta mañana.',
    'Comparan las propuestas de los candidatos en %2$s, incluida la de %1$s.',
    '%1$s respondió preguntas sobre %2$s durante la rueda de prensa.'
  ];
  tpl_gen text[] := array[
    'La situación de %2$s preocupa de cara a las elecciones.',
    'Se debate sobre %2$s en la región.',
    'Buenas señales en %2$s, se nota el avance.',
    'Reporte sobre %2$s y su impacto en la campaña.'
  ];

  -- Picos de conversación: día relativo -> (topic, sentimiento dominante, mult)
  spike_day   int[]  := array[63, 45, 70, 30];
  spike_topic text[] := array['corrupcion','economia','seguridad','salud'];
  spike_sent  text[] := array['negative','negative','negative','positive'];
  spike_mult  real[] := array[2.6, 1.9, 2.2, 1.6];
  v_spike_idx int;
begin
  select array_agg(id order by sort), array_agg(name order by sort) into topic_ids, topic_names from topics;
  select array_agg(id order by sort), array_agg(name order by sort) into actor_ids, actor_names from actors;

  if topic_ids is null or actor_ids is null then
    raise exception 'Faltan topics o actors: ejecuta primero 01_schema.sql';
  end if;

  delete from mentions;

  for d in 0 .. (p_days - 1) loop
    -- ¿Hay pico este día?
    v_spike_idx := null;
    for j in 1 .. array_length(spike_day, 1) loop
      if spike_day[j] = d then v_spike_idx := j; end if;
    end loop;

    -- Volumen del día (tendencia creciente + ruido), amplificado si hay pico.
    v_count := greatest(5, (p_per_day * (1.0 + 0.5 * d::real / p_days) * (0.8 + random() * 0.4))::int);
    if v_spike_idx is not null then
      v_count := (v_count * spike_mult[v_spike_idx])::int;
    end if;

    for i in 1 .. v_count loop
      -- Fuente por peso
      v_r := random(); v_cum := 0; v_source := src_ids[1];
      for j in 1 .. array_length(src_ids, 1) loop
        v_cum := v_cum + src_w[j];
        if v_r <= v_cum then v_source := src_ids[j]; v_eng := src_emin[j] + (random() * (src_emax[j] - src_emin[j]))::int; exit; end if;
      end loop;

      -- Actor (15% conversación genérica)
      if random() < 0.15 then
        v_actor_id := null; v_actor_name := null; v_actor_idx := null;
      else
        v_r := random(); v_cum := 0; v_actor_idx := 1;
        for j in 1 .. array_length(actor_ids, 1) loop
          v_cum := v_cum + coalesce(sov_w[j], 0.1);
          if v_r <= v_cum then v_actor_idx := j; exit; end if;
        end loop;
        v_actor_id := actor_ids[v_actor_idx];
        v_actor_name := actor_names[v_actor_idx];
      end if;

      -- Temática (sesgada al pico si aplica)
      if v_spike_idx is not null and random() < 0.55 then
        v_topic_id := spike_topic[v_spike_idx];
        v_topic_name := (select name from topics where id = v_topic_id);
      else
        j := 1 + floor(random() * array_length(topic_ids, 1))::int;
        v_topic_id := topic_ids[j]; v_topic_name := topic_names[j];
      end if;
      if v_topic_name is null then v_topic_name := v_topic_id; end if;

      -- Sentimiento
      if v_spike_idx is not null and random() < 0.6 then
        v_sentiment := spike_sent[v_spike_idx];
      elsif v_actor_idx is not null then
        v_r := random();
        if v_r < lean_pos[((v_actor_idx - 1) % 4) + 1] then v_sentiment := 'positive';
        elsif v_r < lean_pos[((v_actor_idx - 1) % 4) + 1] + lean_neu[((v_actor_idx - 1) % 4) + 1] then v_sentiment := 'neutral';
        else v_sentiment := 'negative'; end if;
      else
        v_r := random();
        v_sentiment := case when v_r < 0.3 then 'positive' when v_r < 0.7 then 'neutral' else 'negative' end;
      end if;

      -- Emoción derivada del sentimiento
      if v_sentiment = 'positive' then v_emotion := (array['alegria','confianza'])[1 + floor(random() * 2)::int];
      elsif v_sentiment = 'negative' then v_emotion := (array['ira','miedo','tristeza'])[1 + floor(random() * 3)::int];
      else v_emotion := (array['confianza', null])[1 + floor(random() * 2)::int]; end if;

      -- Texto
      if v_actor_id is null then
        v_text := format((tpl_gen)[1 + floor(random() * array_length(tpl_gen, 1))::int], '', lower(v_topic_name));
      elsif v_sentiment = 'positive' then
        v_text := format((tpl_pos)[1 + floor(random() * array_length(tpl_pos, 1))::int], v_actor_name, lower(v_topic_name));
      elsif v_sentiment = 'negative' then
        v_text := format((tpl_neg)[1 + floor(random() * array_length(tpl_neg, 1))::int], v_actor_name, lower(v_topic_name));
      else
        v_text := format((tpl_neu)[1 + floor(random() * array_length(tpl_neu, 1))::int], v_actor_name, lower(v_topic_name));
      end if;

      v_reach := v_eng * (8 + floor(random() * 32)::int) + (case when v_source = 'news' then 50000 else 0 end);
      v_pub := (now()::date - (p_days - 1 - d))::timestamptz
               + make_interval(hours => 1 + floor(random() * 22)::int, mins => floor(random() * 60)::int);

      insert into mentions (source, external_id, author, text, url, lang, published_at,
                            engagement, reach, sentiment, sentiment_score, emotion, topic, actors)
      values (
        v_source,
        'demo-' || d || '-' || i || '-' || floor(random() * 1e9)::bigint,
        case when v_source = 'news'
             then (array['Diario Nacional','Radio Capital','Portal Noticias','El Observador'])[1 + floor(random() * 4)::int]
             else '@' || (array['ciudadano','ana','carlos','votante','maria','juan','analista'])[1 + floor(random() * 7)::int] || floor(random() * 9999)::int end,
        v_text, null, 'es', v_pub, v_eng, v_reach, v_sentiment,
        round((case when v_sentiment = 'positive' then 0.25 + random() * 0.65
                    when v_sentiment = 'negative' then -(0.25 + random() * 0.65)
                    else (random() - 0.5) * 0.24 end)::numeric, 3),
        v_emotion, v_topic_id,
        case when v_actor_id is null then '{}'::text[] else array[v_actor_id] end
      );
      v_total := v_total + 1;
    end loop;
  end loop;

  return v_total;
end;
$$;

-- Ejecuta la siembra (≈ 75 días, ~60 menciones/día con picos)
select seed_demo_data(75, 60) as menciones_creadas;
