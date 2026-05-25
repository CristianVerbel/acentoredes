# Setup en Supabase (web, sin terminal)

Estos scripts montan el **Monitor Electoral** sobre Supabase (Postgres). Solo
necesitas el **SQL Editor** del panel de Supabase.

## Pasos

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. En **SQL Editor → New query**, copia/pega y ejecuta **en orden**:
   1. **`01_schema.sql`** — tablas (`mentions`, `actors`, `topics`, `sources`,
      `project_info`), índices, RLS (lectura pública) y el contexto electoral.
   2. **`02_functions.sql`** — funciones de analítica que el dashboard consume
      vía `supabase.rpc(...)`: `get_config`, `get_summary`, `get_timeline`,
      `get_topics`, `get_sources`, `get_share_of_voice`, `get_emotions`,
      `get_mentions`.
   3. **`03_seed_demo.sql`** — crea y ejecuta `seed_demo_data()` para llenar la
      base con menciones simuladas.
3. En **Project Settings → API** copia el **Project URL** y la clave
   **anon public**. Úsalas como variables de entorno del frontend
   (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) en Vercel.

## Personalizar la elección

Edita los `insert` de `01_schema.sql` (o las tablas `actors`/`topics`/`sources`
desde el **Table Editor**) para tus candidatos, partidos y temáticas.

## Re-sembrar / limpiar

```sql
select seed_demo_data(75, 60);   -- (días, menciones por día)
delete from mentions;            -- vaciar menciones
```

## Filtros disponibles en las funciones

Todas las funciones de lectura aceptan los mismos parámetros opcionales:
`p_from`, `p_to` (fecha ISO), `p_source`, `p_actor`, `p_topic`, `p_sentiment`,
`p_q` (búsqueda de texto). `get_mentions` añade `p_limit`, `p_offset` y `p_sort`
(`recent` | `engagement` | `reach`).

## Seguridad

- La clave **anon** es pública; el acceso está limitado por las políticas
  **RLS** (solo `SELECT`). Las escrituras se hacen desde el SQL Editor.
- No uses la clave **service_role** en el frontend.
