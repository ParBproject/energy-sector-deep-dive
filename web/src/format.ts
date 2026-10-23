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
