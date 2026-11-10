import type { Segment } from "./design/tokens";

export const SEGMENT_LABELS: Record<Segment, string> = {
  majors: "Majors",
  upstream: "E&P",
  midstream: "Midstream",
  refiners: "Refiners",
  services: "Services",
};
export const RATIO_LABELS: Record<string, string> = {
  capex_intensity: "Capex / revenue",
  reinvestment_rate: "Capex / CFO",
  fcf_yield: "FCF yield",
  debt_to_capital: "Debt / capital",
  payout_ratio: "Payout / CFO",
};
export const VIEW_LABELS: Record<string, string> = {
  overview: "Overview",
  returns: "Returns",
  fundamentals: "Fundamentals",
  clusters: "Clusters",
  factors: "Factor model",
  scenario: "Scenario",
};
export const pct = (x: number | null | undefined, d = 1) => (x == null ? "n/a" : `${(x * 100).toFixed(d)}%`);
export const signed = (x: number, d = 1) => `${x >= 0 ? "+" : ""}${x.toFixed(d)}%`;
export const usdBn = (x: number | null | undefined) =>
  x == null ? "n/a" : `$${(x / 1e9).toLocaleString("en-US", { maximumFractionDigits: x < 1e10 ? 1 : 0 })}bn`;

/** Observation / filing dates on an export, with the pull date kept separate. */
export interface Vintage {
  observation_date?: string;
  published?: string;
  published_as?: "filed" | "published";
  retrieved_at?: string;
}

/**
 * Primary date is the latest observation. A filing or publish date follows when the source
 * recorded one. The pull date is last, so it cannot be read as "current through the download".
 */
export function vintageStamp(v: Vintage, source?: string): string {
  const parts: string[] = [];
  if (v.observation_date) parts.push(`Data as of ${v.observation_date}`);
  if (v.published) parts.push(`${v.published_as === "filed" ? "filed" : "published"} ${v.published}`);
  if (v.retrieved_at) parts.push(`retrieved ${v.retrieved_at.slice(0, 10)}`);
  if (source) parts.push(`Source: ${source}`);
  return parts.join(" · ");
}

/** One EIA series. ``retrievedAt`` is the pull (``eia.json`` ``retrieved_at`` or ``as_of``). */
export function eiaStamp(
  series: { observation_date: string; published?: string; published_as?: Vintage["published_as"] },
  retrievedAt: string,
): string {
  return vintageStamp(
    {
      observation_date: series.observation_date,
      published: series.published,
      published_as: series.published_as,
      retrieved_at: retrievedAt,
    },
    "U.S. EIA",
  );
}
