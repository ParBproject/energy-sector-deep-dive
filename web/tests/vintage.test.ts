import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { eiaStamp, vintageStamp, type Vintage } from "../src/format";

const read = (f: string) => JSON.parse(readFileSync(new URL(`../public/data/${f}`, import.meta.url), "utf8"));

const ISO = /^\d{4}-\d{2}-\d{2}$/;

function assertPullIsSecondary(v: Vintage) {
  const stamp = vintageStamp(v, "src");
  expect(stamp.startsWith(`Data as of ${v.observation_date}`)).toBe(true);
  expect(stamp).toContain(`retrieved ${v.retrieved_at}`);
  expect(stamp.indexOf(`Data as of ${v.observation_date}`)).toBeLessThan(stamp.indexOf("retrieved"));
  if (v.published) {
    const label = v.published_as === "filed" ? "filed" : "published";
    expect(stamp).toContain(`${label} ${v.published}`);
    expect(stamp.indexOf(`${label} ${v.published}`)).toBeLessThan(stamp.indexOf("retrieved"));
  }
  if (v.shares?.observation_date) {
    expect(stamp).toContain(`shares as of ${v.shares.observation_date}`);
    expect(stamp.indexOf("shares as of")).toBeGreaterThan(stamp.indexOf(`Data as of ${v.observation_date}`));
    expect(stamp.indexOf("shares as of")).toBeLessThan(stamp.indexOf("retrieved"));
  }
}

describe("export vintages", () => {
  const index = read("index.json");

  it("stamps the observation first and the pull date after it", () => {
    const rigs = { observation_date: "2026-02-28", published: "2026-04-01", published_as: "published" as const };
    expect(eiaStamp(rigs, "2026-10-23T15:30:00+00:00")).toBe(
      "Data as of 2026-02-28 · published 2026-04-01 · retrieved 2026-10-23 · Source: U.S. EIA",
    );
    expect(eiaStamp({ observation_date: "2026-02-28" }, "2026-10-23")).toBe(
      "Data as of 2026-02-28 · retrieved 2026-10-23 · Source: U.S. EIA",
    );
    expect(vintageStamp({ observation_date: "2025-12-31", published: "2026-02-26", published_as: "filed", retrieved_at: "2026-10-23" }, "SEC")).toBe(
      "Data as of 2025-12-31 · filed 2026-02-26 · retrieved 2026-10-23 · Source: SEC",
    );
    expect(vintageStamp({
      observation_date: "2025-12-31",
      published: "2026-02-26",
      published_as: "filed",
      shares: { observation_date: "2026-07-31", published: "2026-08-06", published_as: "filed" },
      retrieved_at: "2026-10-23",
    }, "SEC")).toBe(
      "Data as of 2025-12-31 · filed 2026-02-26 · shares as of 2026-07-31, filed 2026-08-06 · retrieved 2026-10-23 · Source: SEC",
    );
  });

  it("gives every dataset an observation date and a publish date only when one exists", () => {
    expect(index.as_of).toBe(index.vintage.observation_date);
    expect(index.vintage.retrieved_at).toBe(index.snapshot_built_at.slice(0, 10));
    expect(index.vintage.observation_date).not.toBe(index.vintage.retrieved_at);
    for (const name of ["yfinance", "fred", "edgar", "famafrench", "forecaster"] as const) {
      expect(index.datasets[name].observation_date).toMatch(ISO);
      expect(index.datasets[name].retrieved_at).toMatch(ISO);
    }
    expect(index.datasets.edgar.published_as).toBe("filed");
    expect(index.datasets.forecaster.published_as).toBe("published");
    expect(index.datasets.fred.published).toBeUndefined();
    expect(index.datasets.famafrench.published).toBeUndefined();
    expect(index.datasets.fred.series.DCOILWTICO.observation_date).toMatch(ISO);
    expect(index.datasets.eia.observation_date).toBeUndefined();
    expect(index.datasets.eia.series.rotary_rigs_us.observation_date < index.datasets.eia.retrieved_at).toBe(true);
    assertPullIsSecondary(index.vintage);
    assertPullIsSecondary(index.datasets.edgar);
    assertPullIsSecondary(index.datasets.forecaster);
  });

  it("stores that vintage on every exported file", () => {
    for (const file of index.files as string[]) {
      const doc = read(file);
      expect(doc.vintage.retrieved_at).toMatch(ISO);
      if (file === "eia.json") {
        expect(doc.as_of).toBe(doc.vintage.retrieved_at);
        for (const series of Object.values(doc.series) as Array<{ observation_date: string; latest_period: string; published?: string }>) {
          expect(series.observation_date).toMatch(ISO);
          expect(series.published).toBeUndefined();
          const stamp = eiaStamp(series, doc.retrieved_at);
          expect(stamp.startsWith(`Data as of ${series.observation_date}`)).toBe(true);
          expect(stamp.indexOf(series.observation_date)).toBeLessThan(stamp.indexOf("retrieved"));
        }
        expect(doc.series.rotary_rigs_us.observation_date < doc.as_of).toBe(true);
        continue;
      }
      expect(doc.vintage.observation_date).toMatch(ISO);
      assertPullIsSecondary(doc.vintage);
    }
    const fund = read("fundamentals.json").vintage;
    const sizing = read("market_sizing.json").vintage;
    expect(fund.published_as).toBe("filed");
    expect(sizing.published_as).toBe("filed");
    expect(fund.observation_date).toBe(sizing.observation_date);
    expect(fund.shares.observation_date > fund.observation_date).toBe(true);
    expect(fund.shares.published > fund.published).toBe(true);
    expect(vintageStamp(fund).indexOf("shares as of")).toBeGreaterThan(vintageStamp(fund).indexOf("filed"));
    expect(read("scenarios.json").vintage.forecaster.published_as).toBe("published");
    expect(read("factor_model.json").vintage.published).toBeUndefined();
  });
});
