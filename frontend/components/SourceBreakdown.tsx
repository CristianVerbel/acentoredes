"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { SourceStat } from "@/lib/types";
import { fullNumber } from "@/lib/format";

const SOURCE_COLORS: Record<string, string> = {
  twitter: "#38bdf8",
  news: "#a78bfa",
  reddit: "#fb923c",
  youtube: "#ef4444",
  tiktok: "#22d3ee",
  instagram: "#ec4899",
};

export default function SourceBreakdown({ data }: { data: SourceStat[] }) {
  return (
    <div className="card">
      <div className="card-title">Distribución por fuente</div>
      <div className="mt-2 flex items-center gap-4">
        <div className="h-44 w-44 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="count" nameKey="label" cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={2}>
                {data.map((d) => (
                  <Cell key={d.source} fill={SOURCE_COLORS[d.source] || "#64748b"} stroke="#0b1120" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1f2937", borderRadius: 8, fontSize: 12 }}
                formatter={(value: any) => fullNumber(Number(value))}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 space-y-1.5">
          {data.map((d) => (
            <div key={d.source} className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2">
                <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: SOURCE_COLORS[d.source] || "#64748b" }} />
                <span className="text-slate-300">{d.label}</span>
              </span>
              <span className="text-slate-400">{fullNumber(d.count)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
