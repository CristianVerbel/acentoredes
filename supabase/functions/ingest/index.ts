// =============================================================================
// Monitor Electoral — Edge Function de ingesta real (Supabase / Deno)
// -----------------------------------------------------------------------------
// Lee fuentes (Noticias/RSS y Reddit gratis; X/Twitter y YouTube con
// credenciales), analiza cada mencion (sentimiento, emocion, tematica, actores)
// y las inserta en la tabla `mentions` (deduplicando por external_id).
//
// Despliegue SIN terminal:
//   Supabase -> Edge Functions -> Deploy a new function -> nombre "ingest"
//   -> pega ESTE archivo -> Deploy.
//
// Secrets (Edge Functions -> Manage secrets), todos opcionales:
//   INGEST_SECRET         -> si lo defines, exige el header x-ingest-key
//   TWITTER_BEARER_TOKEN  -> habilita el conector de X/Twitter
//   YOUTUBE_API_KEY       -> habilita el conector de YouTube
//   ANTHROPIC_API_KEY     -> habilita analisis con Claude (si USE_LLM=true)
//   USE_LLM               -> "true" para usar el LLM (por defecto: reglas)
// SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY se inyectan automaticamente.
//
// Invocacion:
//   POST/GET  https://<proyecto>.functions.supabase.co/ingest?limit=50
//   (opcional) header x-ingest-key: <INGEST_SECRET>, query ?source=news
// =============================================================================

import { createClient } from "npm:@supabase/supabase-js@2.106.2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-ingest-key",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

// ----------------------------------------------------------------------------
// Tipos
// ----------------------------------------------------------------------------
interface RawMention {
  source: string;
  text: string;
  published_at: string; // ISO
  external_id: string;
  author?: string | null;
  url?: string | null;
  lang?: string;
  engagement?: number;
  reach?: number;
}

interface TopicCfg { id: string; keywords: string[] }
interface ActorCfg { id: string; name: string; aliases: string[] }

// ----------------------------------------------------------------------------
// Analizador por reglas (espanol) — portado del backend Python
// ----------------------------------------------------------------------------
const POSITIVE = new Set([
  "bueno","buena","excelente","gran","mejor","apoyo","apoyamos","ganar","ganamos",
  "esperanza","propuesta","propuestas","logro","logros","exito","felicidades",
  "orgullo","confianza","honesto","transparente","solucion","soluciones","avance",
  "progreso","favor","votare","votaremos","lider","fuerte","positivo","acierto",
  "respeto","admirable","increible","bien",
]);
const NEGATIVE = new Set([
  "malo","mala","peor","corrupto","corrupcion","mentira","mentiroso","fraude","robo",
  "robar","ladron","fracaso","crisis","desastre","verguenza","rechazo","rechazamos",
  "miedo","inseguridad","violencia","incompetente","promesas","populista","demagogo",
  "escandalo","decepcion","decepcionante","engano","traicion","nefasto","pesimo",
  "terrible","indignante","abuso",
]);
const NEGATIONS = new Set(["no","nunca","jamas","ni","tampoco","sin"]);
const EMOTIONS: Record<string, Set<string>> = {
  ira: new Set(["corrupto","fraude","robo","ladron","verguenza","indignante","abuso","traicion","rabia","furia"]),
  miedo: new Set(["miedo","inseguridad","violencia","crisis","amenaza","temor","peligro"]),
  alegria: new Set(["esperanza","felicidades","orgullo","exito","logro","ganamos","celebrar"]),
  tristeza: new Set(["decepcion","fracaso","decepcionante","pena","triste","lamentable"]),
  confianza: new Set(["confianza","honesto","transparente","lider","respeto","creible"]),
};

function normalize(text: string): string {
  return text.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}
function tokenize(norm: string): string[] {
  return norm.match(/[a-z@#]+/g) ?? [];
}

interface Analysis {
  sentiment: string;
  sentiment_score: number;
  emotion: string | null;
  topic: string | null;
  actors: string[];
}

function ruleAnalyze(text: string, topics: TopicCfg[], actors: ActorCfg[]): Analysis {
  const norm = normalize(text);
  const tokens = tokenize(norm);

  // Sentimiento con ventana de negacion
  let raw = 0, hits = 0;
  for (let i = 0; i < tokens.length; i++) {
    let pol = POSITIVE.has(tokens[i]) ? 1 : NEGATIVE.has(tokens[i]) ? -1 : 0;
    if (pol === 0) continue;
    const window = tokens.slice(Math.max(0, i - 2), i);
    if (window.some((w) => NEGATIONS.has(w))) pol *= -1;
    raw += pol; hits += 1;
  }
  const score = hits === 0 ? 0 : Math.max(-1, Math.min(1, raw / (hits + 1)));
  const sentiment = score > 0.15 ? "positive" : score < -0.15 ? "negative" : "neutral";

  // Emocion
  const tokenSet = new Set(tokens);
  let emotion: string | null = null, bestHits = 0;
  for (const [emo, words] of Object.entries(EMOTIONS)) {
    let c = 0;
    for (const w of words) if (tokenSet.has(w)) c++;
    if (c > bestHits) { bestHits = c; emotion = emo; }
  }
  if (!emotion) emotion = sentiment === "positive" ? "alegria" : sentiment === "negative" ? "ira" : null;

  // Tematica
  let topic: string | null = null, topicHits = 0;
  for (const t of topics) {
    let c = 0;
    for (const k of t.keywords) { const nk = normalize(k); if (nk && norm.includes(nk)) c++; }
    if (c > topicHits) { topicHits = c; topic = t.id; }
  }

  // Actores
  const found: string[] = [];
  for (const a of actors) {
    const aliases = [a.name, ...(a.aliases ?? [])];
    if (aliases.some((al) => { const na = normalize(al); return na && norm.includes(na); })) found.push(a.id);
  }

  return { sentiment, sentiment_score: Math.round(score * 1e4) / 1e4, emotion, topic, actors: found };
}

// ----------------------------------------------------------------------------
// Analizador con LLM (opcional) — Claude via fetch
// ----------------------------------------------------------------------------
async function llmAnalyze(
  text: string, topics: TopicCfg[], actors: ActorCfg[], apiKey: string,
): Promise<Analysis> {
  try {
    const topicsDesc = topics.map((t) => t.id).join(", ");
    const actorsDesc = actors.map((a) => `${a.id} (${a.name})`).join(", ");
    const prompt =
      "Eres un analista de escucha digital para una eleccion. Clasifica el texto y " +
      "responde SOLO con JSON.\n" +
      `Tematicas validas (usa el id): ${topicsDesc}\n` +
      `Actores validos (usa el id, lista vacia si no aplica): ${actorsDesc}\n` +
      'Devuelve: {"sentiment":"positive|neutral|negative","sentiment_score":num -1..1,' +
      '"emotion":"ira|miedo|alegria|tristeza|confianza|null","topic":"id|null","actors":["ids"]}\n' +
      `Texto: ${JSON.stringify(text)}`;
    const resp = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-20250514",
        max_tokens: 300,
        messages: [{ role: "user", content: prompt }],
      }),
    });
    const data = await resp.json();
    let payload: string = data?.content?.[0]?.text ?? "";
    payload = payload.slice(payload.indexOf("{"), payload.lastIndexOf("}") + 1);
    const parsed = JSON.parse(payload);
    return {
      sentiment: parsed.sentiment ?? "neutral",
      sentiment_score: Number(parsed.sentiment_score ?? 0),
      emotion: parsed.emotion || null,
      topic: parsed.topic || null,
      actors: Array.isArray(parsed.actors) ? parsed.actors : [],
    };
  } catch {
    return ruleAnalyze(text, topics, actors);
  }
}

// ----------------------------------------------------------------------------
// Conectores
// ----------------------------------------------------------------------------
function decodeEntities(s: string): string {
  return s
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&#x27;/g, "'")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ").trim();
}
function tag(block: string, name: string): string {
  const m = block.match(new RegExp(`<${name}[^>]*>([\\s\\S]*?)</${name}>`, "i"));
  return m ? decodeEntities(m[1]) : "";
}

async function fetchNews(feeds: string[], limit: number): Promise<RawMention[]> {
  const out: RawMention[] = [];
  const perFeed = Math.max(1, Math.floor(limit / Math.max(1, feeds.length)));
  for (const feed of feeds) {
    try {
      const res = await fetch(feed, { headers: { "user-agent": "acentoredes-monitor/0.1" } });
      const xml = await res.text();
      const isAtom = /<entry[\s>]/i.test(xml) && !/<item[\s>]/i.test(xml);
      const blocks = xml.match(isAtom ? /<entry[\s\S]*?<\/entry>/gi : /<item[\s\S]*?<\/item>/gi) ?? [];
      for (const b of blocks.slice(0, perFeed)) {
        const title = tag(b, "title");
        const desc = tag(b, isAtom ? "summary" : "description");
        const text = `${title}. ${desc}`.trim();
        if (text.length < 4) continue;
        let link = tag(b, "link");
        if (isAtom && !link) { const m = b.match(/<link[^>]*href="([^"]+)"/i); link = m ? m[1] : ""; }
        const dateStr = tag(b, "pubDate") || tag(b, "published") || tag(b, "updated");
        const guid = tag(b, "guid") || tag(b, "id") || link;
        out.push({
          source: "news",
          external_id: `news-${guid || link || title}`,
          author: null,
          text: text.slice(0, 4000),
          url: link || null,
          published_at: toISO(dateStr),
          reach: 50000,
          engagement: 0,
        });
      }
    } catch (_e) { /* feed inaccesible: se omite */ }
  }
  return out.slice(0, limit);
}

async function fetchReddit(subreddits: string[], limit: number): Promise<RawMention[]> {
  const out: RawMention[] = [];
  const perSub = Math.max(1, Math.floor(limit / Math.max(1, subreddits.length)));
  for (const sub of subreddits) {
    try {
      const res = await fetch(`https://www.reddit.com/r/${sub}/new.json?limit=${perSub}`, {
        headers: { "user-agent": "acentoredes-monitor/0.1 (escucha digital)" },
      });
      const data = await res.json();
      for (const child of data?.data?.children ?? []) {
        const p = child.data ?? {};
        const text = `${p.title ?? ""}. ${p.selftext ?? ""}`.trim();
        if (text.length < 4) continue;
        out.push({
          source: "reddit",
          external_id: p.name ?? `reddit-${p.id}`,
          author: p.author ?? null,
          text: text.slice(0, 4000),
          url: p.permalink ? `https://reddit.com${p.permalink}` : null,
          published_at: new Date((p.created_utc ?? 0) * 1000).toISOString(),
          engagement: (p.ups ?? 0) + (p.num_comments ?? 0),
          reach: (p.ups ?? 0) * 10,
        });
      }
    } catch (_e) { /* sub inaccesible: se omite */ }
  }
  return out.slice(0, limit);
}

async function fetchTwitter(queryTerms: string[], token: string, limit: number): Promise<RawMention[]> {
  try {
    const query = `(${(queryTerms.length ? queryTerms : ["elecciones"]).join(" OR ")}) lang:es -is:retweet`;
    const params = new URLSearchParams({
      query,
      max_results: String(Math.min(100, Math.max(10, limit))),
      "tweet.fields": "created_at,public_metrics,lang",
      expansions: "author_id",
      "user.fields": "username",
    });
    const res = await fetch(`https://api.twitter.com/2/tweets/search/recent?${params}`, {
      headers: { authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    const users: Record<string, string> = {};
    for (const u of data?.includes?.users ?? []) users[u.id] = u.username;
    return (data?.data ?? []).map((t: any) => {
      const m = t.public_metrics ?? {};
      const eng = (m.like_count ?? 0) + (m.retweet_count ?? 0) + (m.reply_count ?? 0);
      return {
        source: "twitter",
        external_id: t.id,
        author: users[t.author_id] ?? null,
        text: t.text ?? "",
        url: `https://x.com/i/web/status/${t.id}`,
        lang: t.lang ?? "es",
        published_at: toISO(t.created_at),
        engagement: eng,
        reach: m.impression_count ?? eng * 20,
      } as RawMention;
    });
  } catch (_e) { return []; }
}

async function fetchYouTube(queryTerms: string[], apiKey: string, limit: number): Promise<RawMention[]> {
  try {
    const params = new URLSearchParams({
      key: apiKey,
      q: (queryTerms.length ? queryTerms : ["elecciones"]).join(" "),
      part: "snippet", type: "video",
      maxResults: String(Math.min(50, Math.max(1, limit))),
      relevanceLanguage: "es", order: "date",
    });
    const res = await fetch(`https://www.googleapis.com/youtube/v3/search?${params}`);
    const data = await res.json();
    const out: RawMention[] = [];
    for (const item of data?.items ?? []) {
      const s = item.snippet ?? {};
      const vid = item.id?.videoId;
      const text = `${s.title ?? ""}. ${s.description ?? ""}`.trim();
      if (!vid || text.length < 4) continue;
      out.push({
        source: "youtube",
        external_id: vid,
        author: s.channelTitle ?? null,
        text,
        url: `https://youtube.com/watch?v=${vid}`,
        published_at: toISO(s.publishedAt),
        reach: 10000,
        engagement: 0,
      });
    }
    return out;
  } catch (_e) { return []; }
}

function toISO(value: string | null | undefined): string {
  if (!value) return new Date().toISOString();
  const d = new Date(value);
  return isNaN(d.getTime()) ? new Date().toISOString() : d.toISOString();
}

// ----------------------------------------------------------------------------
// Handler
// ----------------------------------------------------------------------------
Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  const ingestSecret = Deno.env.get("INGEST_SECRET");
  if (ingestSecret && req.headers.get("x-ingest-key") !== ingestSecret) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(req.url);
  const limit = Math.min(200, Math.max(1, Number(url.searchParams.get("limit") ?? 50)));
  const onlySource = url.searchParams.get("source");

  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const supabase = createClient(supabaseUrl, serviceKey, { auth: { persistSession: false } });

  // Configuracion desde la base
  const [{ data: topics }, { data: actors }, { data: sources }] = await Promise.all([
    supabase.from("topics").select("id, keywords"),
    supabase.from("actors").select("id, name, aliases"),
    supabase.from("sources").select("id, enabled, config"),
  ]);
  const topicCfg = (topics ?? []) as TopicCfg[];
  const actorCfg = (actors ?? []) as ActorCfg[];

  const useLlm = Deno.env.get("USE_LLM") === "true";
  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  const twitterToken = Deno.env.get("TWITTER_BEARER_TOKEN");
  const youtubeKey = Deno.env.get("YOUTUBE_API_KEY");

  const inserted: Record<string, number> = {};
  const skipped: Record<string, string> = {};

  for (const src of (sources ?? []) as any[]) {
    if (onlySource && src.id !== onlySource) continue;
    if (!src.enabled) { skipped[src.id] = "deshabilitada"; continue; }

    const cfg = src.config ?? {};
    let raw: RawMention[] = [];
    try {
      if (src.id === "news") raw = await fetchNews(cfg.feeds ?? [], limit);
      else if (src.id === "reddit") raw = await fetchReddit(cfg.subreddits ?? [], limit);
      else if (src.id === "twitter") {
        if (!twitterToken) { skipped[src.id] = "sin TWITTER_BEARER_TOKEN"; continue; }
        raw = await fetchTwitter(cfg.query_terms ?? [], twitterToken, limit);
      } else if (src.id === "youtube") {
        if (!youtubeKey) { skipped[src.id] = "sin YOUTUBE_API_KEY"; continue; }
        raw = await fetchYouTube(cfg.query_terms ?? [], youtubeKey, limit);
      } else { skipped[src.id] = "sin conector"; continue; }
    } catch (e) {
      skipped[src.id] = `error: ${String(e)}`;
      continue;
    }

    const rows = [];
    for (const m of raw) {
      const a = useLlm && anthropicKey
        ? await llmAnalyze(m.text, topicCfg, actorCfg, anthropicKey)
        : ruleAnalyze(m.text, topicCfg, actorCfg);
      rows.push({
        source: m.source,
        external_id: m.external_id,
        author: m.author ?? null,
        text: m.text,
        url: m.url ?? null,
        lang: m.lang ?? "es",
        published_at: m.published_at,
        engagement: m.engagement ?? 0,
        reach: m.reach ?? 0,
        sentiment: a.sentiment,
        sentiment_score: a.sentiment_score,
        emotion: a.emotion,
        topic: a.topic,
        actors: a.actors,
      });
    }

    if (rows.length) {
      const { error, count } = await supabase
        .from("mentions")
        .upsert(rows, { onConflict: "external_id", ignoreDuplicates: true, count: "exact" });
      if (error) skipped[src.id] = `insert error: ${error.message}`;
      else inserted[src.id] = count ?? rows.length;
    } else {
      inserted[src.id] = 0;
    }
  }

  return json({ ok: true, inserted, skipped, analysis: useLlm && anthropicKey ? "llm" : "rules" });
});

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "content-type": "application/json" },
  });
}
