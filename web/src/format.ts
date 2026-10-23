import type { Segment } from "./design/tokens";

export const SEGMENT_LABELS: Record<Segment, string> = {
  majors: "Majors",
  upstream: "E&P",
  midstream: "Midstream",
  refiners: "Refiners",
  services: "Services",
};
export const pct = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;
export const signed = (x: number, d = 1) => `${x >= 0 ? "+" : ""}${x.toFixed(d)}%`;
export const usdBn = (x: number) => `$${(x / 1e9).toLocaleString("en-US", { maximumFractionDigits: 0 })}bn`;
