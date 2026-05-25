"use client";

import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimelinePoint } from "@/lib/types";

export default function SentimentTimeline({ data }: { data: TimelinePoint[] }) {
  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.date).toLocaleDateString("es", { day: "2-digit", month: "short" }),
  }));

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="card-title">Evolución de la conversación</div>
        <div className="muted">Volumen diario y sentimiento neto</div>
      </div>
      <div className="mt-3 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formatted} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#94a3b8" }} interval="preserveStartEnd" minTickGap={28} />
            <YAxis yAxisId="left" tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[-100, 100]}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
            />
            <Tooltip
              contentStyle={{ background: "#0f172a", border: "1px solid #1f2937", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#e2e8f0" }}
            />
            <Area yAxisId="left" type="monotone" dataKey="total" name="Volumen" stroke="#38bdf8" fill="url(#vol)" />
            <Bar yAxisId="left" dataKey="negative" name="Negativas" fill="#dc2626" opacity={0.65} barSize={6} />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="net_sentiment"
              name="Sentimiento neto"
              stroke="#facc15"
              strokeWidth={2}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
