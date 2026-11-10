import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { eiaStamp } from "../src/format";

const pub = JSON.parse(readFileSync(new URL("../public/data/eia.json", import.meta.url), "utf8"));
const meta = JSON.parse(readFileSync(new URL("../../data/snapshot/eia_meta.json", import.meta.url), "utf8"));

describe("EIA data in the explorer", () => {
  it("stamps each series with its observation date and keeps the pull date secondary", () => {
    expect(pub.as_of).toBe(meta.as_of);
    expect(pub.vintage.retrieved_at).toBe(meta.as_of);
    for (const [k, s] of Object.entries(pub.series) as [string, { observation_date: string }][]) {
      expect(s.observation_date).toBe(meta.series[k].observation_date);
      expect(eiaStamp(s, pub.retrieved_at)).toBe(
        `Data as of ${s.observation_date} · retrieved ${meta.as_of} · Source: U.S. EIA`,
      );
      expect(eiaStamp(s, pub.retrieved_at)).not.toBe(`Data as of ${meta.as_of} · Source: U.S. EIA`);
    }
  });
  it("exports every snapshot series with matching latest period and aligned arrays", () => {
    expect(Object.keys(pub.series).sort()).toEqual(Object.keys(meta.series).sort());
    for (const [k, s] of Object.entries(pub.series) as [string, { dates: string[]; values: number[]; latest_period: string; series_id: string; observation_date: string }][]) {
      expect(s.dates.length).toBe(s.values.length);
      expect(s.dates.length).toBe(meta.series[k].rows);
      expect(s.latest_period).toBe(meta.series[k].latest_period);
      expect(s.observation_date).toBe(meta.series[k].observation_date);
      expect(s.series_id).toBe(meta.series[k].series_id);
      expect(s.values.every((v) => Number.isFinite(v))).toBe(true);
    }
  });
});
