import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { eiaStamp } from "../src/format";

const pub = JSON.parse(readFileSync(new URL("../public/data/eia.json", import.meta.url), "utf8"));
const meta = JSON.parse(readFileSync(new URL("../../data/snapshot/eia_meta.json", import.meta.url), "utf8"));

describe("EIA data in the explorer", () => {
  it("as-of date shown equals the committed snapshot metadata", () => {
    expect(pub.as_of).toBe(meta.as_of);
    expect(eiaStamp(pub)).toBe(`Data as of ${meta.as_of} · Source: U.S. EIA`);
  });
  it("exports every snapshot series with matching latest period and aligned arrays", () => {
    expect(Object.keys(pub.series).sort()).toEqual(Object.keys(meta.series).sort());
    for (const [k, s] of Object.entries(pub.series) as [string, { dates: string[]; values: number[]; latest_period: string; series_id: string }][]) {
      expect(s.dates.length).toBe(s.values.length);
      expect(s.dates.length).toBe(meta.series[k].rows);
      expect(s.latest_period).toBe(meta.series[k].latest_period);
      expect(s.series_id).toBe(meta.series[k].series_id);
      expect(s.values.every((v) => Number.isFinite(v))).toBe(true);
    }
  });
});
