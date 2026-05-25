"use client";

import type { Mention, MonitorConfig } from "@/lib/types";
import { SENTIMENT_COLORS, SENTIMENT_LABELS, compactNumber, formatDate } from "@/lib/format";

export default function MentionsFeed({
  mentions,
  config,
}: {
  mentions: Mention[];
  config: MonitorConfig;
}) {
  const topicName = (id: string | null) =>
    config.topics.find((t) => t.id === id)?.name ?? id ?? "—";
  const sourcelabel = (id: string) => config.sources[id]?.label ?? id;

  return (
    <div className="card flex h-full flex-col">
      <div className="card-title">Menciones recientes</div>
      <div className="mt-3 flex-1 space-y-2 overflow-y-auto pr-1" style={{ maxHeight: 560 }}>
        {mentions.length === 0 ? (
          <div className="muted py-8 text-center">Sin menciones para los filtros actuales.</div>
        ) : (
          mentions.map((m) => (
            <div key={m.id} className="rounded-lg border border-white/5 bg-white/[0.03] p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs">
                  <span
                    className="chip"
                    style={{ background: `${SENTIMENT_COLORS[m.sentiment]}22`, color: SENTIMENT_COLORS[m.sentiment] }}
                  >
                    {SENTIMENT_LABELS[m.sentiment]}
                  </span>
                  <span className="text-slate-400">{sourcelabel(m.source)}</span>
                  <span className="text-slate-500">·</span>
                  <span className="text-slate-400">{m.author ?? "anónimo"}</span>
                </div>
                <span className="muted">{formatDate(m.published_at)}</span>
              </div>
              <p className="mt-2 text-sm text-slate-200">{m.text}</p>
              <div className="muted mt-2 flex flex-wrap items-center gap-2">
                <span className="rounded bg-white/5 px-1.5 py-0.5">{topicName(m.topic)}</span>
                {m.actors.map((a) => (
                  <span key={a} className="rounded bg-sky-500/10 px-1.5 py-0.5 text-sky-300">
                    {config.actors.find((x) => x.id === a)?.name ?? a}
                  </span>
                ))}
                <span className="ml-auto">{compactNumber(m.engagement)} interacciones</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
