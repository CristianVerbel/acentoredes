import { supabase } from "./supabase";
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

// Convierte los filtros del dashboard en los parámetros de las funciones RPC.
function params(f: Filters, extra: Record<string, unknown> = {}) {
  return {
    p_from: f.from ?? null,
    p_to: f.to ?? null,
    p_source: f.source ?? null,
    p_actor: f.actor ?? null,
    p_topic: f.topic ?? null,
    p_sentiment: f.sentiment ?? null,
    p_q: f.q ?? null,
    ...extra,
  };
}

async function rpc<T>(fn: string, args: Record<string, unknown>): Promise<T> {
  const { data, error } = await supabase.rpc(fn, args);
  if (error) throw new Error(`${fn}: ${error.message}`);
  return data as T;
}

export const api = {
  config: () => rpc<MonitorConfig>("get_config", {}),
  summary: (f: Filters) => rpc<Summary>("get_summary", params(f)),
  timeline: (f: Filters) => rpc<TimelinePoint[]>("get_timeline", params(f)),
  topics: (f: Filters) => rpc<TopicStat[]>("get_topics", params(f)),
  sources: (f: Filters) => rpc<SourceStat[]>("get_sources", params(f)),
  shareOfVoice: (f: Filters) => rpc<ShareOfVoiceItem[]>("get_share_of_voice", params(f)),
  emotions: (f: Filters) => rpc<EmotionStat[]>("get_emotions", params(f)),
  mentions: (f: Filters, limit = 40, sort = "recent") =>
    rpc<MentionsPage>("get_mentions", params(f, { p_limit: limit, p_offset: 0, p_sort: sort })),
};
