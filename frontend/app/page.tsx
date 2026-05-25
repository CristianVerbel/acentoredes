"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type {
  EmotionStat,
  Filters,
  Mention,
  MonitorConfig,
  ShareOfVoiceItem,
  SourceStat,
  Summary,
  TimelinePoint,
  TopicStat,
} from "@/lib/types";
import FilterBar from "@/components/FilterBar";
import KpiCards from "@/components/KpiCards";
import SentimentTimeline from "@/components/SentimentTimeline";
import ShareOfVoice from "@/components/ShareOfVoice";
import TopicsChart from "@/components/TopicsChart";
import SourceBreakdown from "@/components/SourceBreakdown";
import EmotionsChart from "@/components/EmotionsChart";
import MentionsFeed from "@/components/MentionsFeed";

interface Data {
  summary: Summary;
  timeline: TimelinePoint[];
  topics: TopicStat[];
  sources: SourceStat[];
  sov: ShareOfVoiceItem[];
  emotions: EmotionStat[];
  mentions: Mention[];
}

function defaultFrom(): string {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.toISOString().slice(0, 10);
}

export default function Page() {
  const [config, setConfig] = useState<MonitorConfig | null>(null);
  const [filters, setFilters] = useState<Filters>({ from: defaultFrom() });
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.config().then(setConfig).catch((e) => setError(String(e)));
  }, []);

  const load = useCallback(async (f: Filters) => {
    setLoading(true);
    try {
      const [summary, timeline, topics, sources, sov, emotions, mentions] = await Promise.all([
        api.summary(f),
        api.timeline(f),
        api.topics(f),
        api.sources(f),
        api.shareOfVoice(f),
        api.emotions(f),
        api.mentions(f, 40, "recent"),
      ]);
      setData({ summary, timeline, topics, sources, sov, emotions, mentions: mentions.items });
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => load(filters), 250);
    return () => clearTimeout(t);
  }, [filters, load]);

  if (error && !data) {
    return (
      <main className="mx-auto max-w-2xl p-10">
        <div className="card">
          <div className="card-title text-negative">No se pudo conectar con Supabase</div>
          <p className="muted mt-2">{error}</p>
          <p className="muted mt-2">
            Verifica que <code>NEXT_PUBLIC_SUPABASE_URL</code> y{" "}
            <code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code> estén configuradas y que hayas ejecutado los
            scripts SQL de la carpeta <code>supabase/</code> (esquema, funciones y datos demo).
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-white md:text-2xl">
            {config?.project.name ?? "Monitor Electoral"}
          </h1>
          <p className="muted">
            Escucha digital · {config?.project.election} · {config?.project.country}
            {config?.llm_analysis ? " · análisis con IA" : " · análisis por reglas"}
          </p>
        </div>
        {loading ? <span className="muted animate-pulse">actualizando…</span> : null}
      </header>

      {config ? <FilterBar config={config} filters={filters} onChange={setFilters} /> : null}

      {data ? (
        <>
          <KpiCards summary={data.summary} />

          <SentimentTimeline data={data.timeline} />

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <TopicsChart data={data.topics} />
            {config ? <ShareOfVoice data={data.sov} /> : null}
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <SourceBreakdown data={data.sources} />
            <EmotionsChart data={data.emotions} />
            <div className="lg:col-span-1">
              {config ? <MentionsFeed mentions={data.mentions} config={config} /> : null}
            </div>
          </div>
        </>
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card h-24 animate-pulse" />
          ))}
        </div>
      )}
    </main>
  );
}
