import { tokens } from "./tokens";

/** Flatten tokens into CSS custom properties so CSS never hard-codes a value. */
export function cssVars(): Record<string, string> {
  const c = tokens.color;
  const v: Record<string, string> = {};
  for (const [k, val] of Object.entries(c)) {
    if (typeof val === "string") v[`--c-${k}`] = val;
  }
  for (const [k, val] of Object.entries(c.segment)) v[`--seg-${k}`] = val;
  for (const [k, val] of Object.entries(tokens.font.size)) v[`--fs-${k}`] = `${val}px`;
  tokens.space.scale.forEach((val, i) => (v[`--sp-${i}`] = `${val}px`));
  for (const [k, val] of Object.entries(tokens.radius)) v[`--r-${k}`] = `${val}px`;
  v["--font-ui"] = tokens.font.ui;
  v["--font-mono"] = tokens.font.mono;
  v["--touch"] = `${tokens.layout.touchTarget}px`;
  v["--gutter"] = `${tokens.layout.gutter}px`;
  v["--max-w"] = `${tokens.layout.maxWidth}px`;
  v["--cols"] = String(tokens.layout.columns);
  v["--ease"] = `cubic-bezier(${tokens.motion.ease.join(",")})`;
  v["--dur"] = `${tokens.motion.base}s`;
  return v;
}

export function applyCssVars(el: HTMLElement = document.documentElement): void {
  for (const [k, val] of Object.entries(cssVars())) el.style.setProperty(k, val);
}
