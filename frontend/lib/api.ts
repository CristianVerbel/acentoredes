import type {
  EmotionStat,
  Filters,
  MentionsPage,
  MonitorConfig,
  ShareOfVoiceItem,
  SourceStat,
  Summary,
  TimelinePoint,
  TopicStat,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function qs(filters: Filters, extra: Record<string, string | number> = {}): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
  });
  Object.entries(extra).forEach(([k, v]) => params.set(k, String(v)));
  const s = params.toString();
  return s ? `?${s}` : "";
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  config: () => get<MonitorConfig>("/api/config"),
  summary: (f: Filters) => get<Summary>(`/api/summary${qs(f)}`),
  timeline: (f: Filters) => get<TimelinePoint[]>(`/api/timeline${qs(f)}`),
  topics: (f: Filters) => get<TopicStat[]>(`/api/topics${qs(f)}`),
  sources: (f: Filters) => get<SourceStat[]>(`/api/sources${qs(f)}`),
  shareOfVoice: (f: Filters) => get<ShareOfVoiceItem[]>(`/api/share-of-voice${qs(f)}`),
  emotions: (f: Filters) => get<EmotionStat[]>(`/api/emotions${qs(f)}`),
  mentions: (f: Filters, limit = 40, sort = "recent") =>
    get<MentionsPage>(`/api/mentions${qs(f, { limit, sort })}`),
};

export { API_URL };
