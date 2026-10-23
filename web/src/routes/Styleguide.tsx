import { useMemo } from "react";
import { ChartCard, Skeleton } from "../components/ChartCard";
import { EChart } from "../components/EChart";
import { contrast } from "../design/contrast";
import { SEGMENTS, textPairs, tokens } from "../design/tokens";
import { SEGMENT_LABELS } from "../format";

const c = tokens.color;
const surfaces = ["bg", "surface1", "surface2", "border", "grid", "accent", "danger"] as const;

export function Styleguide() {
  const demo = useMemo(
    () => ({
      xAxis: { type: "category", data: SEGMENTS.map((s) => SEGMENT_LABELS[s]) },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: SEGMENTS.map((s, i) => ({ value: [0.35, 0.55, 0.31, 0.27, 0.4][i], itemStyle: { color: c.segment[s] } })) }],
    }),
    [],
  );
  return (
    <main className="container sg">
      <header className="topbar">
        <h1 className="brand">
          Styleguide<small>All values from web/src/design/tokens.ts</small>
        </h1>
        <a className="btn linkbtn" href="#/">
          ← App
        </a>
      </header>
      <section>
        <h2>Surfaces &amp; accent</h2>
        <div className="grid12">
          {surfaces.map((k) => (
            <div className="swatch span-3" key={k}>
              <div className="fill" style={{ background: c[k] }} />
              <div className="meta"><strong>{k}</strong> <span className="num">{c[k]}</span></div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>Segment palette (colour-blind safe)</h2>
        <div className="grid12">
          {SEGMENTS.map((s) => (
            <div className="swatch span-3" key={s}>
              <div className="fill" style={{ background: c.segment[s] }} />
              <div className="meta"><strong>{SEGMENT_LABELS[s]}</strong> <span className="num">{c.segment[s]} · {contrast(c.segment[s], c.surface1).toFixed(1)}:1</span></div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>Text contrast (WCAG AA ≥ 4.5)</h2>
        <div className="grid12">
          {textPairs.map(([fg, bg]) => (
            <div className="swatch span-3" key={fg + bg} style={{ background: c[bg] as string, padding: 12 }}>
              <span style={{ color: c[fg] as string }}>{fg} on {bg}</span>{" "}
              <span className="num" style={{ color: c[fg] as string }}>{contrast(c[fg] as string, c[bg] as string).toFixed(2)}:1</span>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2>Type scale · Inter / JetBrains Mono</h2>
        {Object.entries(tokens.font.size).reverse().map(([k, v]) => (
          <div key={k} style={{ fontSize: v, lineHeight: 1.3, marginBottom: 8 }}>
            {k} {v}px · Oil beta <span className="num">0.551 1,278.09</span>
          </div>
        ))}
      </section>
      <section>
        <h2>12-column grid · 8 px spacing</h2>
        <div className="grid12">
          {Array.from({ length: 12 }, (_, i) => (
            <div className="gridcol span-1 num" style={{ gridColumn: "span 1" }} key={i}>{i + 1}</div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "end", marginTop: 16 }}>
          {tokens.space.scale.slice(1).map((v) => (
            <div key={v} style={{ width: v, height: v, background: c.accent, borderRadius: 2 }} title={`${v}px`} />
          ))}
        </div>
      </section>
      <section>
        <h2>Components</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
          <button className="btn primary">Primary</button>
          <button className="btn">Secondary</button>
          <button className="chip" aria-pressed="true"><span className="dot" style={{ background: c.segment.upstream }} />Selected chip</button>
          <button className="chip" aria-pressed="false"><span className="dot" style={{ background: c.segment.majors }} />Chip</button>
        </div>
        <div className="grid12">
          <ChartCard id="sg-chart" title="Chart card" description="ECharts with the registered theme." source="tokens demo" asOf="2026-10-22">
            <EChart option={demo} label="Demo bar chart" />
          </ChartCard>
          <ChartCard id="sg-skel" title="Loading state" description="Skeleton loader while data arrives." source="—" loading>
            <Skeleton />
          </ChartCard>
        </div>
      </section>
    </main>
  );
}
