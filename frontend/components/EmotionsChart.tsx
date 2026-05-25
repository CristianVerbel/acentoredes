"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import type { EmotionStat } from "@/lib/types";
import { EMOTION_LABELS } from "@/lib/format";

const EMOTION_COLORS: Record<string, string> = {
  ira: "#ef4444",
  miedo: "#a855f7",
  alegria: "#22c55e",
  tristeza: "#3b82f6",
  confianza: "#14b8a6",
};

export default function EmotionsChart({ data }: { data: EmotionStat[] }) {
  const rows = data.map((d) => ({ ...d, label: EMOTION_LABELS[d.emotion] || d.emotion }));

  return (
    <div className="card">
      <div className="card-title">Emociones dominantes</div>
      <div className="mt-3 h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#cbd5e1" }} />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              contentStyle={{ background: "#0f172a", border: "1px solid #1f2937", borderRadius: 8, fontSize: 12 }}
            />
            <Bar dataKey="count" name="Menciones" radius={[4, 4, 0, 0]}>
              {rows.map((d) => (
                <Cell key={d.emotion} fill={EMOTION_COLORS[d.emotion] || "#64748b"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
