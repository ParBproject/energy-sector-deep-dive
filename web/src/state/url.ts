import { SEGMENTS, type Segment } from "../design/tokens";

export const VIEWS = ["overview", "returns", "fundamentals", "clusters", "factors", "scenario"] as const;
export type View = (typeof VIEWS)[number] | "styleguide";
export type OilSource = "slider" | "forecaster";

/** The part of the store that is shareable by link. */
export interface UrlState {
  view: View;
  segments: Segment[];
  company: string | null;
  pins: string[];
  range: [string, string] | null;
  oil: number;
  oilSource: OilSource;
}

export const DEFAULT_URL_STATE: UrlState = {
  view: "overview",
  segments: [...SEGMENTS],
  company: null,
  pins: [],
  range: null,
  oil: -10,
  oilSource: "slider",
};

export const MAX_PINS = 4;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const TICKER = /^[A-Z.=^]{1,6}$/;

/** State -> "#/view?seg=..&co=..". Defaults are omitted to keep links short. */
export function serialize(s: UrlState): string {
  const q = new URLSearchParams();
  if (s.segments.length !== SEGMENTS.length) q.set("seg", s.segments.join(","));
  if (s.company) q.set("co", s.company);
  if (s.pins.length) q.set("pin", s.pins.join(","));
  if (s.range) q.set("range", `${s.range[0]}_${s.range[1]}`);
  if (s.oil !== DEFAULT_URL_STATE.oil) q.set("oil", String(s.oil));
  if (s.oilSource !== DEFAULT_URL_STATE.oilSource) q.set("src", s.oilSource);
  const qs = q.toString().replace(/%2C/g, ",");
  return `#/${s.view}${qs ? `?${qs}` : ""}`;
}

/** "#/view?..." -> state. Invalid values fall back to defaults instead of throwing. */
export function parse(hash: string): UrlState {
  const [path, qs = ""] = hash.replace(/^#\/?/, "").split("?");
  const q = new URLSearchParams(qs);
  const view = ([...VIEWS, "styleguide"] as string[]).includes(path) ? (path as View) : DEFAULT_URL_STATE.view;
  const segs = (q.get("seg") ?? "").split(",").filter((x): x is Segment => (SEGMENTS as string[]).includes(x));
  const co = q.get("co");
  const pins = [...new Set((q.get("pin") ?? "").split(",").filter((x) => TICKER.test(x)))].slice(0, MAX_PINS);
  const [from, to] = (q.get("range") ?? "").split("_");
  const range: [string, string] | null = DATE.test(from ?? "") && DATE.test(to ?? "") && from < to ? [from, to] : null;
  const oilRaw = Number(q.get("oil"));
  const oil = q.has("oil") && Number.isFinite(oilRaw) ? Math.max(-50, Math.min(50, oilRaw)) : DEFAULT_URL_STATE.oil;
  const src = q.get("src") === "forecaster" ? "forecaster" : "slider";
  return {
    view,
    segments: segs.length ? SEGMENTS.filter((s) => segs.includes(s)) : [...SEGMENTS],
    company: co && TICKER.test(co) ? co : null,
    pins,
    range,
    oil,
    oilSource: src,
  };
}
