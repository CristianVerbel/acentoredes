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
│  X / YT /    │   │  sentimiento + tema  │   │  (SQLite)     │   │  Next.js    │
│  Reddit/RSS  │   │  + emoción + actores │   │               │   │  + Recharts │
└──────────────┘   └──────────────────────┘   └───────────────┘   └─────────────┘
        ingesta            FastAPI / Python                            React
```

> **Estado:** dashboard funcional con **datos demo**. Las APIs oficiales de
> redes suelen ser pagas/limitadas; el monitor viene sembrado con datos de
> ejemplo y con conectores listos para enchufar credenciales reales.

---

## Arquitectura

| Capa | Tecnología | Carpeta |
|------|------------|---------|
| Backend / API | Python · FastAPI · SQLAlchemy | [`backend/`](backend/) |
| Frontend / Dashboard | Next.js · React · Recharts · Tailwind | [`frontend/`](frontend/) |
| Contexto electoral | YAML configurable | [`config/election.yaml`](config/election.yaml) |

El **contexto** (candidatos, partidos, temáticas y fuentes) es **genérico y
configurable**: edita `config/election.yaml` para adaptarlo a cualquier
elección o país, sin tocar código.

---

## Inicio rápido (demo)

Requisitos: **Python 3.11+** y **Node.js 20+**.

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

Edita [`config/election.yaml`](config/election.yaml):

- **`actors`** — candidatos/partidos a monitorear, con sus `aliases` (variantes
  de texto y @usuarios) para detectar menciones.
- **`topics`** — temáticas (economía, seguridad, salud…) con `keywords` para
  clasificar cada mención.
- **`sources`** — qué fuentes habilitar y sus parámetros (feeds RSS,
  subreddits, términos de búsqueda).

Tras editar, reinicia el backend y vuelve a sembrar/ingerir.

---

## Conectar fuentes reales

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

## Endpoints principales de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/config` | Contexto electoral (actores, temáticas, fuentes) |
| GET | `/api/summary` | KPIs: volumen, sentimiento neto, alcance… |
| GET | `/api/timeline` | Evolución diaria de volumen y sentimiento |
| GET | `/api/topics` | Estadísticas por temática |
| GET | `/api/sources` | Estadísticas por fuente |
| GET | `/api/share-of-voice` | Share of voice y sentimiento por actor |
| GET | `/api/emotions` | Distribución de emociones |
| GET | `/api/mentions` | Feed de menciones (paginado, filtrable) |
| POST | `/api/ingest` | Dispara una ronda de ingesta real |

Todos los endpoints de lectura aceptan filtros por query string:
`from`, `to`, `source`, `actor`, `topic`, `sentiment`, `q` (búsqueda de texto).

---

## Estructura del proyecto

```
acentoredes/
├── config/
│   └── election.yaml          # Contexto electoral configurable
├── backend/                   # API FastAPI
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
├── frontend/                  # Dashboard Next.js
│   ├── app/                   # Página principal + layout
│   ├── components/            # Gráficos y widgets (Recharts)
│   └── lib/                   # Cliente de API, tipos, formato
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
- Las credenciales viven en `backend/.env` (ignorado por git). Nunca las subas.
