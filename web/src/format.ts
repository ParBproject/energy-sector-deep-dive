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
export interface DatedFact {
  observation_date?: string;
  published?: string;
  published_as?: "filed" | "published";
}
export interface Vintage extends DatedFact {
  retrieved_at?: string;
  /** Later cover-page share count. Shown after the annual-flow date, before the pull date. */
  shares?: DatedFact;
}

function publishedClause(v: DatedFact): string | undefined {
  if (!v.published) return undefined;
  return `${v.published_as === "filed" ? "filed" : "published"} ${v.published}`;
}

/**
 * Primary date is the observation the chart's main numbers use. A filing or publish date
 * follows when the source recorded one. A later share count, then the pull date, come after
 * that, so neither can be read as the date of the annual figures.
 */
export function vintageStamp(v: Vintage, source?: string): string {
  const parts: string[] = [];
  if (v.observation_date) parts.push(`Data as of ${v.observation_date}`);
  const filed = publishedClause(v);
  if (filed) parts.push(filed);
  const shares = v.shares;
  if (shares?.observation_date && shares.observation_date !== v.observation_date) {
    const shareFiled = publishedClause(shares);
    parts.push(`shares as of ${shares.observation_date}${shareFiled ? `, ${shareFiled}` : ""}`);
  }
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
