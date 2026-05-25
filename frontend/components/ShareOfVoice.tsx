"use client";

import type { ShareOfVoiceItem } from "@/lib/types";
import { compactNumber, netColor } from "@/lib/format";

export default function ShareOfVoice({ data }: { data: ShareOfVoiceItem[] }) {
  const max = Math.max(1, ...data.map((d) => d.count));

  return (
    <div className="card">
      <div className="card-title">Share of voice por actor</div>
      <div className="muted">Volumen de menciones y sentimiento neto</div>
      <div className="mt-4 space-y-3">
        {data.map((a) => (
          <div key={a.actor_id}>
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: a.color }} />
                <span className="font-medium text-slate-200">{a.name}</span>
                {a.party ? <span className="muted">· {a.party}</span> : null}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-slate-300">{a.share}%</span>
                <span style={{ color: netColor(a.net_sentiment) }} className="font-semibold">
                  {a.net_sentiment > 0 ? "+" : ""}
                  {a.net_sentiment}
                </span>
              </div>
            </div>
            <div className="mt-1 h-5 w-full overflow-hidden rounded bg-white/5">
              <div
                className="flex h-full overflow-hidden rounded"
                style={{ width: `${(a.count / max) * 100}%`, minWidth: a.count > 0 ? "2%" : 0 }}
              >
                <div style={{ flex: a.positive, background: "#16a34a" }} />
                <div style={{ flex: a.neutral, background: "#64748b" }} />
                <div style={{ flex: a.negative, background: "#dc2626" }} />
              </div>
            </div>
            <div className="muted mt-0.5 flex justify-between">
              <span>{compactNumber(a.count)} menciones</span>
              <span>alcance {compactNumber(a.total_reach)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
