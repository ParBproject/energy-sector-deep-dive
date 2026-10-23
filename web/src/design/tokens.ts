/**
 * Single source of design tokens for the explorer AND the Python README charts.
 * `npm run tokens` writes ./tokens.json, which src/analysis/charts.py reads.
 */
export const tokens = {
  color: {
    // near-black base + two raised surfaces
    bg: "#0A0D12",
    surface1: "#111720",
    surface2: "#18202B",
    border: "#263241",
    grid: "#1D2632",
    text: "#E6EAF0",
    textMuted: "#A3AEBD",
    textSubtle: "#8693A5",
    accent: "#10B981", // selection, primary line, focus rings
    accentStrong: "#34D399",
    onAccent: "#04140E",
    danger: "#F87171",
    // muted Okabe-Ito derived palette: colour-blind safe, distinct from the accent
    segment: {
      majors: "#7FB8E0",
      upstream: "#E3A857",
      midstream: "#C99BC0",
      refiners: "#D8CF73",
      services: "#E08A6A",
    },
  },
  font: {
    ui: "'Inter Variable', Inter, system-ui, sans-serif",
    mono: "'JetBrains Mono Variable', 'JetBrains Mono', ui-monospace, monospace",
    // 12 / 14 / 16 / 20 / 28 / 40
    size: { xs: 12, sm: 14, md: 16, lg: 20, xl: 28, xxl: 40 },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
    lineHeight: { tight: 1.2, normal: 1.5 },
  },
  space: { unit: 8, scale: [0, 4, 8, 16, 24, 32, 48, 64] },
  layout: { columns: 12, gutter: 16, maxWidth: 1280, mobile: 390, touchTarget: 44 },
  radius: { sm: 6, md: 10, lg: 16 },
  motion: { fast: 0.15, base: 0.25, slow: 0.4, ease: [0.2, 0.8, 0.2, 1] as number[] },
} as const;

/** Text/background pairs used in the UI; every one must meet WCAG AA (4.5:1). */
export const textPairs: Array<[keyof typeof tokens.color, keyof typeof tokens.color]> = [
  ["text", "bg"],
  ["text", "surface1"],
  ["text", "surface2"],
  ["textMuted", "bg"],
  ["textMuted", "surface1"],
  ["textMuted", "surface2"],
  ["textSubtle", "bg"],
  ["textSubtle", "surface1"],
  ["accent", "bg"],
  ["accent", "surface1"],
  ["accent", "surface2"],
  ["onAccent", "accent"],
];

export type Segment = keyof typeof tokens.color.segment;
export const SEGMENTS = Object.keys(tokens.color.segment) as Segment[];
