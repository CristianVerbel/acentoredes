# Acento Redes — Monitor Electoral de Escucha Digital

Herramienta de **escucha digital (social listening)** para leer qué dice la
población en redes sociales y medios, con un **monitor de temáticas y
sentimiento** sobre una elección.

Ingesta menciones de varias fuentes (X/Twitter, YouTube, Reddit, Noticias/RSS),
las analiza (sentimiento, emoción, temática y actores políticos mencionados) y
las expone en un **dashboard** interactivo con KPIs, evolución temporal, share
of voice por candidato, agenda de temáticas, emociones y un feed de menciones.

```
┌──────────────┐   ┌──────────────────────┐   ┌───────────────┐   ┌─────────────┐
│  Conectores  │ → │  Análisis            │ → │  Base de datos│ → │  Dashboard  │
│  X / YT /    │   │  sentimiento + tema  │   │  Supabase     │   │  Next.js    │
│  Reddit/RSS  │   │  + emoción + actores │   │  (Postgres)   │   │  + Recharts │
└──────────────┘   └──────────────────────┘   └───────────────┘   └─────────────┘
                                                  funciones SQL        React
```

> **Estado:** dashboard funcional con **datos demo**. Las APIs oficiales de
> redes suelen ser pagas/limitadas; el monitor viene sembrado con datos de
> ejemplo y con conectores listos para enchufar credenciales reales.

---

## Dos formas de montarlo

| Opción | Cómo | Ideal si… |
|--------|------|-----------|
| **A — Web, sin terminal** (recomendada) | **Supabase** (base de datos + analítica en SQL) + **Vercel** (dashboard). Todo desde paneles web. | No quieres usar la línea de comandos. |
| **B — Local** | Backend **Python/FastAPI** + frontend Next.js en tu máquina. | Quieres correr conectores e ingesta tú mismo. |

El **contexto** (candidatos, partidos, temáticas) es **genérico y configurable**
en ambos casos.

---

## Opción A — Web, sin terminal (Supabase + Vercel)

No necesitas instalar nada ni usar la terminal. Todo se hace en paneles web.

### 1. Crear el proyecto en Supabase

1. Entra a [supabase.com](https://supabase.com) → **New project** (plan gratuito sirve).
2. Espera a que la base de datos quede lista (~1–2 min).

### 2. Cargar el esquema, las funciones y los datos demo (SQL Editor)

En el panel de Supabase abre **SQL Editor → New query**, y ejecuta **en este orden**
el contenido de la carpeta [`supabase/`](supabase/) (copia y pega cada archivo, luego **Run**):

1. [`supabase/01_schema.sql`](supabase/01_schema.sql) — tablas, seguridad y contexto electoral.
2. [`supabase/02_functions.sql`](supabase/02_functions.sql) — funciones de analítica que consume el dashboard.
3. [`supabase/03_seed_demo.sql`](supabase/03_seed_demo.sql) — genera ~4.500 menciones demo.

Al terminar el paso 3 verás el número de menciones creadas. Listo: ya tienes datos.

### 3. Copiar las llaves del proyecto

En Supabase → **Project Settings → API**, copia:
- **Project URL** (ej. `https://xxxx.supabase.co`)
- La clave **anon public** (es segura de exponer; el acceso está limitado por RLS).

### 4. Desplegar el dashboard en Vercel (importando este repo)

1. Sube/usa este repositorio en GitHub.
2. Entra a [vercel.com](https://vercel.com) → **Add New… → Project** → importa el repo.
3. En **Root Directory** selecciona **`frontend`**.
4. En **Environment Variables** añade:
   - `NEXT_PUBLIC_SUPABASE_URL` = el Project URL de Supabase
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = la clave anon public
5. **Deploy**. Al terminar tendrás la URL pública del monitor. 🎉

> Si cambias datos o configuración en Supabase, el dashboard se actualiza solo
> (lee en tiempo real). Solo necesitas redeploy si cambias variables de entorno.

### Re-sembrar o limpiar datos

Desde el SQL Editor de Supabase:

```sql
select seed_demo_data(75, 60);   -- re-genera datos demo (días, menciones/día)
delete from mentions;            -- vacía las menciones
```

---

## Opción B — Local (Python/FastAPI + Next.js)

Requisitos: **Python 3.11+** y **Node.js 20+**.

> Nota: el frontend de este repo está configurado para **Supabase** (Opción A).
> Para usarlo contra el backend local de FastAPI, apunta `lib/api.ts` a la API
> REST (`/api/...`) en lugar de a las funciones RPC de Supabase.

### 1. Backend (API + datos demo)

```bash
cd backend
pip install -r requirements.txt

# Sembrar datos demo (menciones simuladas de ~75 días)
python -m scripts.seed_demo --days 75 --per-day 60 --reset

# Levantar la API en http://localhost:8000
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva de la API en `http://localhost:8000/docs`.

### 2. Frontend (dashboard)

En otra terminal:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Abre `http://localhost:3000`.

---

## Configurar la elección

**Opción A (Supabase):** edita las tablas `actors`, `topics` y `sources` desde
el **Table Editor** de Supabase, o cambia los `insert` de
[`supabase/01_schema.sql`](supabase/01_schema.sql) antes de ejecutarlo. El
dashboard refleja los cambios automáticamente.

**Opción B (local):** edita [`config/election.yaml`](config/election.yaml):

- **`actors`** — candidatos/partidos a monitorear, con sus `aliases` (variantes
  de texto y @usuarios) para detectar menciones.
- **`topics`** — temáticas (economía, seguridad, salud…) con `keywords` para
  clasificar cada mención.
- **`sources`** — qué fuentes habilitar y sus parámetros (feeds RSS,
  subreddits, términos de búsqueda).

Tras editar, reinicia el backend y vuelve a sembrar/ingerir.

---

## Conectar fuentes reales

### En Supabase (web, sin terminal) — Edge Function

La carpeta [`supabase/functions/ingest`](supabase/functions/ingest) trae una
**Edge Function** (Deno) que lee fuentes, analiza cada mención y la guarda en
`mentions`. **Noticias/RSS** y **Reddit** funcionan gratis; **X/Twitter** y
**YouTube** se activan con credenciales (secrets). Despliégala desde el panel
(**Edge Functions → Deploy a new function → `ingest`**, pega el archivo) y, si
quieres, prográmala con [`supabase/04_schedule.sql`](supabase/04_schedule.sql).
Detalle paso a paso en [`supabase/README.md`](supabase/README.md). Las fuentes y
sus parámetros (feeds, subreddits, términos) se editan en la tabla `sources`.

### En local (Opción B) — conectores Python

Los conectores viven en [`backend/app/connectors/`](backend/app/connectors/) y
comparten una interfaz común. Cada uno se activa al proveer sus credenciales en
`backend/.env` (ver [`backend/.env.example`](backend/.env.example)):

| Fuente | Conector | Requiere |
|--------|----------|----------|
| Noticias / RSS | `news.py` | `pip install feedparser` (gratis) |
| Reddit / Foros | `reddit.py` | Nada para demo (endpoint JSON público) |
| X / Twitter | `twitter.py` | `TWITTER_BEARER_TOKEN` (API v2) |
| YouTube | `youtube.py` | `YOUTUBE_API_KEY` (Data API v3) |
| TikTok / Instagram | (patrón análogo) | Acceso de partner/API |

Una fuente sin credenciales queda **"no disponible"** y la ingesta la omite;
el monitor sigue funcionando con los datos demo. Para disparar una ronda de
ingesta real:

```bash
curl -X POST "http://localhost:8000/api/ingest?limit_per_source=100"
```

### Análisis con IA (opcional)

Por defecto el análisis usa un **analizador por reglas** (léxico en español +
palabras clave), sin dependencias externas. Para un análisis más preciso con
Claude, en `backend/.env`:

```
USE_LLM_ANALYSIS=true
ANTHROPIC_API_KEY=sk-ant-...
```

Si el LLM falla por cualquier motivo, el sistema cae de vuelta al analizador por
reglas para no detenerse.

---

## API: REST (Python) y RPC (Supabase)

El dashboard consume la misma analítica en ambas opciones. En Supabase son
**funciones RPC** (`supabase.rpc(...)`); en el backend Python son **endpoints REST**.

| Analítica | REST (Python) | RPC (Supabase) |
|-----------|---------------|----------------|
| Contexto (actores/temáticas/fuentes) | `GET /api/config` | `get_config()` |
| KPIs / resumen | `GET /api/summary` | `get_summary(...)` |
| Evolución temporal | `GET /api/timeline` | `get_timeline(...)` |
| Temáticas | `GET /api/topics` | `get_topics(...)` |
| Fuentes | `GET /api/sources` | `get_sources(...)` |
| Share of voice | `GET /api/share-of-voice` | `get_share_of_voice(...)` |
| Emociones | `GET /api/emotions` | `get_emotions(...)` |
| Feed de menciones | `GET /api/mentions` | `get_mentions(...)` |
| Ingesta real | `POST /api/ingest` | (job externo / Edge Function) |

Todas aceptan los mismos filtros: fecha (`from`/`to`), `source`, `actor`,
`topic`, `sentiment` y `q` (búsqueda de texto).

---

## Estructura del proyecto

```
acentoredes/
├── supabase/                  # Opción A: setup web (SQL para el SQL Editor)
│   ├── 01_schema.sql          # Tablas, RLS y contexto electoral
│   ├── 02_functions.sql       # Funciones de analítica (RPC)
│   ├── 03_seed_demo.sql       # Generador de datos demo en SQL
│   ├── 04_schedule.sql        # (Opcional) cron para la ingesta
│   └── functions/ingest/      # Edge Function de ingesta real (Deno/TS)
├── config/
│   └── election.yaml          # Contexto electoral (Opción B / local)
├── backend/                   # Opción B: API FastAPI
│   ├── app/
│   │   ├── main.py            # App + routers + CORS
│   │   ├── config.py          # Settings + carga de election.yaml
│   │   ├── database.py        # SQLAlchemy
│   │   ├── models.py          # Modelo Mention
│   │   ├── schemas.py         # Esquemas de respuesta
│   │   ├── queries.py         # Agregaciones analíticas
│   │   ├── ingest.py          # Orquestador de ingesta
│   │   ├── analysis/          # Sentimiento/tema (reglas + LLM opcional)
│   │   ├── connectors/        # X, YouTube, Reddit, RSS
│   │   └── routers/           # analytics, mentions, meta
│   └── scripts/seed_demo.py   # Generador de datos demo
├── frontend/                  # Dashboard Next.js (Supabase)
│   ├── app/                   # Página principal + layout
│   ├── components/            # Gráficos y widgets (Recharts)
│   └── lib/                   # Cliente Supabase, API, tipos, formato
└── README.md
```

---

## Integración con WhatsApp (OpenClaw)

El repositorio también incluye una integración de **OpenClaw + WhatsApp**
(`docker-compose.yml`, `openclaw.config.yaml`, `setup.sh`). Puede usarse como
**canal de alertas** del monitor —por ejemplo, notificar picos de menciones
negativas a un grupo— o de forma independiente. Ver
[`openclaw.config.yaml`](openclaw.config.yaml) y `setup.sh`.

---

## Notas

- Los datos demo son **simulados** y solo sirven para visualizar el dashboard.
- Respeta los Términos de Servicio de cada plataforma al ingerir datos reales.
- La clave **anon** de Supabase es pública por diseño; el acceso lo limita
  **RLS** (en el SQL se habilita solo lectura). Nunca expongas la clave
  **service_role** en el frontend.
- Las credenciales del backend local viven en `backend/.env` (ignorado por git).
