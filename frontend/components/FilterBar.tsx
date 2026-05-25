"use client";

import type { Filters, MonitorConfig } from "@/lib/types";

const RANGES = [
  { label: "7 días", days: 7 },
  { label: "30 días", days: 30 },
  { label: "90 días", days: 90 },
  { label: "Todo", days: 0 },
];

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export default function FilterBar({
  config,
  filters,
  onChange,
}: {
  config: MonitorConfig;
  filters: Filters;
  onChange: (f: Filters) => void;
}) {
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch });

  const activeRange =
    filters.from === undefined ? 0 : Math.round((Date.now() - new Date(filters.from).getTime()) / 86400000);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex overflow-hidden rounded-lg border border-white/10">
        {RANGES.map((r) => {
          const active = r.days === 0 ? !filters.from : Math.abs(activeRange - r.days) <= 1;
          return (
            <button
              key={r.label}
              onClick={() => set({ from: r.days === 0 ? undefined : isoDaysAgo(r.days) })}
              className={`px-3 py-1.5 text-xs font-medium transition ${
                active ? "bg-sky-500 text-white" : "bg-white/5 text-slate-300 hover:bg-white/10"
              }`}
            >
              {r.label}
            </button>
          );
        })}
      </div>

      <Select
        value={filters.source ?? ""}
        onChange={(v) => set({ source: v || undefined })}
        placeholder="Todas las fuentes"
        options={Object.entries(config.sources).map(([id, s]) => ({ value: id, label: s.label }))}
      />
      <Select
        value={filters.actor ?? ""}
        onChange={(v) => set({ actor: v || undefined })}
        placeholder="Todos los actores"
        options={config.actors.map((a) => ({ value: a.id, label: a.name }))}
      />
      <Select
        value={filters.topic ?? ""}
        onChange={(v) => set({ topic: v || undefined })}
        placeholder="Todas las temáticas"
        options={config.topics.map((t) => ({ value: t.id, label: t.name }))}
      />
      <Select
        value={filters.sentiment ?? ""}
        onChange={(v) => set({ sentiment: v || undefined })}
        placeholder="Todo sentimiento"
        options={[
          { value: "positive", label: "Positivo" },
          { value: "neutral", label: "Neutral" },
          { value: "negative", label: "Negativo" },
        ]}
      />

      <input
        value={filters.q ?? ""}
        onChange={(e) => set({ q: e.target.value || undefined })}
        placeholder="Buscar texto…"
        className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:border-sky-500 focus:outline-none"
      />
    </div>
  );
}

function Select({
  value,
  onChange,
  placeholder,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value} className="bg-slate-900">
          {o.label}
        </option>
      ))}
    </select>
  );
}
