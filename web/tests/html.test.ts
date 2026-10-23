import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
const loader = readFileSync(new URL("../src/data/load.ts", import.meta.url), "utf8");

describe("index.html", () => {
  it("preloads every data file the app fetches", () => {
    const fetched = [...loader.matchAll(/get<[^>]+>\("([^"]+\.json)"\)/g)].map((m) => m[1]).sort();
    const preloaded = [...html.matchAll(/rel="preload" href="%BASE_URL%data\/([^"]+)"/g)].map((m) => m[1]).sort();
    expect(fetched.length).toBeGreaterThan(5);
    expect(preloaded).toEqual(fetched);
  });
  it("has lang, a description and a favicon (Lighthouse SEO / best practices)", () => {
    expect(html).toMatch(/<html lang="en">/);
    expect(html).toMatch(/<meta name="description" content="[^"]{50,}"/);
    expect(html).toMatch(/<link rel="icon"/);
  });
});
