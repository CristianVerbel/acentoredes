export const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#16a34a",
  neutral: "#94a3b8",
  negative: "#dc2626",
};

export const SENTIMENT_LABELS: Record<string, string> = {
  positive: "Positivo",
  neutral: "Neutral",
  negative: "Negativo",
};

export const EMOTION_LABELS: Record<string, string> = {
  ira: "Ira",
  miedo: "Miedo",
  alegria: "Alegría",
  tristeza: "Tristeza",
  confianza: "Confianza",
};

export function compactNumber(n: number): string {
  return new Intl.NumberFormat("es", { notation: "compact", maximumFractionDigits: 1 }).format(n);
}

export function fullNumber(n: number): string {
  return new Intl.NumberFormat("es").format(n);
}

export function netColor(net: number): string {
  if (net > 3) return "#16a34a";
  if (net < -3) return "#dc2626";
  return "#94a3b8";
}

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("es", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
