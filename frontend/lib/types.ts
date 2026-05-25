export type Sentiment = "positive" | "neutral" | "negative";

export interface Actor {
  id: string;
  name: string;
  type: string;
  party: string | null;
  color: string;
  aliases: string[];
}

export interface Topic {
  id: string;
  name: string;
  keywords: string[];
}

export interface SourceMeta {
  label: string;
  enabled: boolean;
  available: boolean;
}

export interface MonitorConfig {
  project: {
    name: string;
    language: string;
    country: string;
    election: string;
    timezone: string;
  };
  actors: Actor[];
  topics: Topic[];
  sources: Record<string, SourceMeta>;
  llm_analysis: boolean;
}

export interface Summary {
  total_mentions: number;
  total_reach: number;
  total_engagement: number;
  sentiment: { positive: number; neutral: number; negative: number };
  avg_sentiment_score: number;
  net_sentiment: number;
  unique_authors: number;
  sources_count: number;
  top_topic: string | null;
  period_start: string | null;
  period_end: string | null;
}

export interface TimelinePoint {
  date: string;
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  net_sentiment: number;
}

export interface TopicStat {
  id: string;
  name: string;
  count: number;
  positive: number;
  neutral: number;
  negative: number;
  net_sentiment: number;
  avg_score: number;
}

export interface SourceStat {
  source: string;
  label: string;
  count: number;
  positive: number;
  neutral: number;
  negative: number;
  net_sentiment: number;
}

export interface ShareOfVoiceItem {
  actor_id: string;
  name: string;
  party: string | null;
  color: string;
  count: number;
  share: number;
  positive: number;
  neutral: number;
  negative: number;
  net_sentiment: number;
  total_reach: number;
}

export interface EmotionStat {
  emotion: string;
  count: number;
}

export interface Mention {
  id: number;
  source: string;
  author: string | null;
  text: string;
  url: string | null;
  lang: string;
  published_at: string;
  engagement: number;
  reach: number;
  sentiment: Sentiment;
  sentiment_score: number;
  emotion: string | null;
  topic: string | null;
  actors: string[];
}

export interface MentionsPage {
  total: number;
  limit: number;
  offset: number;
  items: Mention[];
}

export interface Filters {
  from?: string;
  to?: string;
  source?: string;
  actor?: string;
  topic?: string;
  sentiment?: string;
  q?: string;
}
