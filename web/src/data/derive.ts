import type { Segment } from "../design/tokens";
import type { AllData, ScenarioResult, TimeSeries } from "./types";

const Z95 = 1.959964;

/** Same maths as src/scenarios/oil.py, so the slider can move continuously. */
export function scenarioAt(s: ScenarioResult, movePct: number) {
  const m = movePct / 100;
  const out = {} as Record<Segment, { expected: number; lo: number; hi: number; predLo: number; predHi: number }>;
  for (const [seg, b] of Object.entries(s.weekly_betas) as [Segment, ScenarioResult["weekly_betas"][Segment]][]) {
    const mid = b.beta * m;
    const half = Z95 * b.se_hac * Math.abs(m);
    const pred = Z95 * Math.sqrt((b.se_hac * m) ** 2 + b.resid_sd ** 2);
    out[seg] = { expected: mid * 100, lo: (mid - half) * 100, hi: (mid + half) * 100, predLo: (mid - pred) * 100, predHi: (mid + pred) * 100 };
  }
  return out;
}

/** Index positions of a date range (inclusive) in the weekly series. */
export function rangeIdx(ts: TimeSeries, range: [string, string] | null): [number, number] {
  if (!range) return [0, ts.dates.length - 1];
  const i0 = Math.max(0, ts.dates.findIndex((d) => d >= range[0]));
  let i1 = ts.dates.length - 1;
  while (i1 > 0 && ts.dates[i1] > range[1]) i1--;
  return [i0, Math.max(i0, i1)];
}

/** Total return over the range from a 100-based index series. */
export function rangeReturn(series: (number | null)[], [i0, i1]: [number, number]): number | null {
  let a: number | null = null;
  for (let i = i0; i <= i1 && a === null; i++) a = series[i];
  const b = series[i1];
  return a && b ? b / a - 1 : null;
}

export function companiesIn(d: AllData, segs: Segment[]): string[] {
  return Object.entries(d.returns.betas.companies)
    .filter(([, v]) => segs.includes(v.segment))
    .map(([t]) => t);
}
