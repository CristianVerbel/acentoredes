"use client";

import type { Summary } from "@/lib/types";
import { compactNumber, fullNumber, netColor } from "@/lib/format";

export default function KpiCards({ summary }: { summary: Summary }) {
  const total = summary.total_mentions || 1;
  const pct = (n: number) => Math.round((n / total) * 100);

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      <Kpi label="Menciones" value={fullNumber(summary.total_mentions)} sub={`${summary.unique_authors} autores`} />
      <Kpi
        label="Sentimiento neto"
        value={`${summary.net_sentiment > 0 ? "+" : ""}${summary.net_sentiment}`}
        valueColor={netColor(summary.net_sentiment)}
        sub="(% pos − % neg)"
      />
      <Kpi label="Alcance estimado" value={compactNumber(summary.total_reach)} sub={`${compactNumber(summary.total_engagement)} interacciones`} />
      <Kpi label="Fuentes activas" value={String(summary.sources_count)} sub={summary.top_topic ? `Top: ${summary.top_topic}` : ""} />
      <div className="card">
        <div className="muted">Distribución</div>
        <div className="mt-2 flex h-3 w-full overflow-hidden rounded-full bg-white/10">
          <div style={{ width: `${pct(summary.sentiment.positive)}%`, background: "#16a34a" }} />
          <div style={{ width: `${pct(summary.sentiment.neutral)}%`, background: "#94a3b8" }} />
          <div style={{ width: `${pct(summary.sentiment.negative)}%`, background: "#dc2626" }} />
        </div>
        <div className="mt-2 flex justify-between text-[11px]">
          <span className="text-positive">{pct(summary.sentiment.positive)}% pos</span>
          <span className="text-neutral">{pct(summary.sentiment.neutral)}% neu</span>
          <span className="text-negative">{pct(summary.sentiment.negative)}% neg</span>
        </div>
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  sub,
  valueColor,
}: {
  label: string;
  value: string;
  sub?: string;
  valueColor?: string;
}) {
  return (
    <div className="card">
      <div className="muted">{label}</div>
      <div className="mt-1 text-2xl font-bold" style={valueColor ? { color: valueColor } : undefined}>
        {value}
      </div>
      {sub ? <div className="muted mt-1 truncate">{sub}</div> : null}
    </div>
  );
}
