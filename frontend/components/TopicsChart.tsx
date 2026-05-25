"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TopicStat } from "@/lib/types";
import { netColor } from "@/lib/format";

export default function TopicsChart({ data }: { data: TopicStat[] }) {
  return (
    <div className="card">
      <div className="card-title">Temáticas de la agenda</div>
      <div className="muted">Volumen por tema, coloreado por sentimiento neto</div>
      <div className="mt-3 h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} />
            <YAxis
              type="category"
              dataKey="name"
              width={120}
              tick={{ fontSize: 11, fill: "#cbd5e1" }}
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              contentStyle={{ background: "#0f172a", border: "1px solid #1f2937", borderRadius: 8, fontSize: 12 }}
              formatter={(value: any, _n: any, item: any) => [
                `${value} menciones · neto ${item.payload.net_sentiment}`,
                item.payload.name,
              ]}
            />
            <Bar dataKey="count" name="Menciones" radius={[0, 4, 4, 0]}>
              {data.map((d) => (
                <Cell key={d.id} fill={netColor(d.net_sentiment)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
