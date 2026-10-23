import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { cssVars } from "../src/design/cssVars";
import { echartsTheme } from "../src/design/echartsTheme";
import { SEGMENTS, tokens } from "../src/design/tokens";

describe("tokens", () => {
  it("uses the emerald accent", () => expect(tokens.color.accent).toBe("#10B981"));
  it("has the 12/14/16/20/28/40 type scale", () =>
    expect(Object.values(tokens.font.size)).toEqual([12, 14, 16, 20, 28, 40]));
  it("uses an 8 px spacing system and a 12-column grid", () => {
    expect(tokens.space.unit).toBe(8);
    expect(tokens.layout.columns).toBe(12);
    for (const v of tokens.space.scale) expect(v % 4).toBe(0);
    expect(tokens.layout.gutter % 8).toBe(0);
  });
  it("has 44 px touch targets", () => expect(tokens.layout.touchTarget).toBeGreaterThanOrEqual(44));
  it("uses self-hosted fonts, no CDN", () => {
    const main = readFileSync(new URL("../src/main.tsx", import.meta.url), "utf8");
    expect(main).toContain("@fontsource-variable/inter");
    expect(main).toContain("@fontsource-variable/jetbrains-mono");
    const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
    expect(html).not.toMatch(/fonts\.googleapis|cdn\./);
  });
  it("tokens.json (read by Python charts) is in sync with tokens.ts", () => {
    const json = JSON.parse(readFileSync(new URL("../src/design/tokens.json", import.meta.url), "utf8"));
    expect(json).toEqual(JSON.parse(JSON.stringify(tokens)));
  });
  it("exposes every token as a CSS variable", () => {
    const v = cssVars();
    expect(v["--c-accent"]).toBe("#10B981");
    for (const s of SEGMENTS) expect(v[`--seg-${s}`]).toBe(tokens.color.segment[s]);
    expect(v["--touch"]).toBe("44px");
  });
  it("registers an ECharts theme built from tokens", () => {
    expect(echartsTheme.color[0]).toBe(tokens.color.accent);
    expect(echartsTheme.color.slice(1)).toEqual(Object.values(tokens.color.segment));
  });
  it("CSS uses variables, not hard-coded hex colours", () => {
    const css = readFileSync(new URL("../src/design/global.css", import.meta.url), "utf8");
    expect(css).not.toMatch(/#[0-9a-fA-F]{3,6}\b/);
  });
});
