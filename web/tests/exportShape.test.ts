import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { SEGMENTS } from "../src/design/tokens";

const read = (f: string) => JSON.parse(readFileSync(new URL(`../public/data/${f}`, import.meta.url), "utf8"));

describe("exported results JSON (make export)", () => {
  const index = read("index.json");
  it("index lists every file (incl. timeseries) with a source and an as-of date", () => {
    expect(index.as_of).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    for (const f of index.files) {
      expect(index.sources[f]).toBeTruthy();
      expect(() => read(f)).not.toThrow();
    }
  });
  it("returns.json has betas for all segments and the three shocks", () => {
    const r = read("returns.json");
    for (const s of SEGMENTS) expect(typeof r.betas.segments[s].beta).toBe("number");
    expect(Object.keys(r.drawdowns)).toHaveLength(3);
    for (const v of Object.values(r.betas.companies) as Array<{ segment: string; ci95: number[] }>) {
      expect(SEGMENTS).toContain(v.segment);
      expect(v.ci95).toHaveLength(2);
    }
  });
  it("scenarios.json has a symmetric grid with bands", () => {
    const s = read("scenarios.json");
    expect(Object.keys(s.grid)).toContain("-10");
    const b = s.grid["-10"].upstream;
    expect(b.param_band_pct[0]).toBeLessThan(b.expected_pct);
    expect(b.param_band_pct[1]).toBeGreaterThan(b.expected_pct);
    expect(s.default_input).toBe("slider");
  });
  it("factor_model.json has walk-forward results for every segment", () => {
    const f = read("factor_model.json");
    for (const s of SEGMENTS) {
      expect(typeof f.walk_forward_explanatory[s].vs_hist_mean).toBe("number");
      expect(typeof f.walk_forward_predictive_lag1[s].vs_hist_mean).toBe("number");
    }
  });
  it("sizing and clustering carry the KPI fields", () => {
    expect(read("market_sizing.json").total_revenue_latest_usd).toBeGreaterThan(0);
    expect(read("clustering.json").k5.kmeans.adjusted_rand_vs_segments).toBeGreaterThan(-1);
  });
});
