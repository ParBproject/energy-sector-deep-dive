import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { rangeIdx, rangeReturn, scenarioAt } from "../src/data/derive";
import { opacityFor } from "../src/charts/options";
import type { ScenarioResult, TimeSeries } from "../src/data/types";

const read = <T>(f: string): T => JSON.parse(readFileSync(new URL(`../public/data/${f}`, import.meta.url), "utf8"));

describe("client-side scenario maths", () => {
  const sc = read<ScenarioResult>("scenarios.json");
  it.each(["-30", "-10", "5", "25"])("matches the Python grid at %s%%", (g) => {
    const js = scenarioAt(sc, Number(g));
    for (const [seg, v] of Object.entries(sc.grid[g])) {
      const k = seg as keyof typeof js;
      expect(js[k].expected).toBeCloseTo(v.expected_pct, 3); // JSON is rounded to 6 dp
      expect(js[k].lo).toBeCloseTo(v.param_band_pct[0], 3); // JSON is rounded to 6 dp
      expect(js[k].hi).toBeCloseTo(v.param_band_pct[1], 3); // JSON is rounded to 6 dp
      expect(js[k].predLo).toBeCloseTo(v.prediction_band_pct[0], 3); // JSON is rounded to 6 dp
    }
  });
});

describe("range helpers", () => {
  const ts = read<TimeSeries>("timeseries.json");
  it("full range when none selected", () => expect(rangeIdx(ts, null)).toEqual([0, ts.dates.length - 1]));
  it("finds inclusive bounds", () => {
    const [i0, i1] = rangeIdx(ts, ["2020-01-01", "2020-12-31"]);
    expect(ts.dates[i0] >= "2020-01-01" && ts.dates[i0 - 1] < "2020-01-01").toBe(true);
    expect(ts.dates[i1] <= "2020-12-31" && ts.dates[i1 + 1] > "2020-12-31").toBe(true);
  });
  it("computes range returns from the index", () => {
    expect(rangeReturn([100, null, 110, 121], [0, 3])).toBeCloseTo(0.21);
    expect(rangeReturn([null, 50, 75], [0, 2])).toBeCloseTo(0.5);
    expect(rangeReturn([null, null], [0, 1])).toBeNull();
  });
});

describe("linked highlighting", () => {
  it("dims everything except the focus and pins", () => {
    expect(opacityFor("XOM", { company: null, pins: [] })).toBe(1);
    expect(opacityFor("XOM", { company: "XOM", pins: [] })).toBe(1);
    expect(opacityFor("CVX", { company: "XOM", pins: [] })).toBeLessThan(0.5);
    expect(opacityFor("CVX", { company: "XOM", pins: ["CVX"] })).toBe(1);
  });
});
