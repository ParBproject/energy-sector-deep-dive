import { describe, expect, it } from "vitest";
import { contrast } from "../src/design/contrast";
import { SEGMENTS, textPairs, tokens } from "../src/design/tokens";

const c = tokens.color;

describe("WCAG contrast", () => {
  it("matches known reference values", () => {
    expect(contrast("#000000", "#FFFFFF")).toBeCloseTo(21, 5);
    expect(contrast("#777777", "#FFFFFF")).toBeCloseTo(4.48, 2);
  });
  it.each(textPairs)("%s on %s passes AA (4.5:1)", (fg, bg) => {
    expect(contrast(c[fg] as string, c[bg] as string)).toBeGreaterThanOrEqual(4.5);
  });
  it.each(SEGMENTS)("segment %s is legible as a graphic on every surface (>= 3:1)", (s) => {
    for (const bg of [c.bg, c.surface1, c.surface2]) expect(contrast(c.segment[s], bg)).toBeGreaterThanOrEqual(3);
  });
  it("segment colours are distinct from the accent and each other", () => {
    const all = [c.accent, ...Object.values(c.segment)];
    expect(new Set(all).size).toBe(all.length);
  });
});
