import type { EChartsCoreOption } from "echarts/core";
import { tokens, type Segment } from "../design/tokens";
import { companiesIn, rangeIdx, rangeReturn, scenarioAt } from "../data/derive";
import { RATIOS, type AllData } from "../data/types";
import { RATIO_LABELS, SEGMENT_LABELS, pct } from "../format";

const c = tokens.color;
const mono = { fontFamily: tokens.font.mono };
const pctAxis = { type: "value", axisLabel: { formatter: "{value}%", ...mono } } as const;

export interface Focus {
  company: string | null;
  pins: string[];
}

/** Linked highlighting: the focused company and pins stay bright, everything else dims. */
export function opacityFor(ticker: string, f: Focus): number {
  if (!f.company && f.pins.length === 0) return 1;
  return ticker === f.company || f.pins.includes(ticker) ? 1 : 0.22;
}
const border = (t: string, f: Focus) =>
  t === f.company ? { borderColor: c.accent, borderWidth: 2 } : f.pins.includes(t) ? { borderColor: c.text, borderWidth: 1 } : {};

const fmtPct = (v: unknown) => `${Number(v).toFixed(1)}%`;

export function heroOption(d: AllData, segs: Segment[], range: [string, string] | null, f: Focus): EChartsCoreOption {
  const { ts } = d;
  const line = (name: string, data: (number | null)[], color: string, extra: object = {}) => ({
    name, type: "line", data, showSymbol: false, lineStyle: { color, width: 1.6 }, itemStyle: { color }, emphasis: { focus: "series" }, ...extra,
  });
  const series = [
    ...segs.map((s) => line(SEGMENT_LABELS[s], ts.segments[s], c.segment[s])),
    line("XLE", ts.symbols.XLE, c.text, { lineStyle: { color: c.text, width: 1.2, type: "dashed" } }),
    line("S&P 500", ts.symbols.SPY, c.textMuted, { lineStyle: { color: c.textMuted, width: 1.2, type: "dotted" } }),
    ...[...new Set([f.company, ...f.pins].filter(Boolean) as string[])].map((t) =>
      line(t, ts.symbols[t], c.accent, { lineStyle: { color: c.accent, width: t === f.company ? 2.6 : 1.4, type: t === f.company ? "solid" : "dashed" }, z: 5 }),
    ),
  ];
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "cross", label: { backgroundColor: c.surface2 } }, valueFormatter: (v: unknown) => (v == null ? "n/a" : Number(v).toFixed(1)) },
    legend: { top: 0, type: "scroll", itemWidth: 14, itemHeight: 2, pageTextStyle: { color: c.textMuted } },
    grid: { top: 40, bottom: 64 },
    xAxis: { type: "category", data: ts.dates, boundaryGap: false, axisLabel: { ...mono, hideOverlap: true } },
    yAxis: { type: "log", logBase: 10, axisLabel: { ...mono }, min: "dataMin" },
    dataZoom: [
      { type: "inside", startValue: range?.[0], endValue: range?.[1] },
      { type: "slider", height: 28, bottom: 8, startValue: range?.[0], endValue: range?.[1], borderColor: c.border, fillerColor: "rgba(16,185,129,0.15)", handleStyle: { color: c.accent }, textStyle: { color: c.textMuted, ...mono }, dataBackground: { lineStyle: { color: c.border }, areaStyle: { color: c.surface2 } } },
    ],
    series,
  };
}

export function oilBetaOption(d: AllData, segs: Segment[], f: Focus): EChartsCoreOption {
  const rows = Object.entries(d.returns.betas.companies).filter(([, v]) => segs.includes(v.segment)).sort((a, b) => a[1].beta - b[1].beta);
  return {
    tooltip: {
      trigger: "item",
      formatter: (p: { name: string }) => {
        const b = d.returns.betas.companies[p.name];
        return `<b>${p.name}</b> · ${SEGMENT_LABELS[b.segment]}<br/>beta ${b.beta.toFixed(2)} (95% CI ${b.ci95[0].toFixed(2)}–${b.ci95[1].toFixed(2)})<br/>R² ${b.r2.toFixed(2)} · n=${b.n}`;
      },
    },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: rows.map(([t]) => t), axisLabel: { ...mono, interval: 0 } },
    series: [{
      type: "bar", barMaxWidth: 14, cursor: "pointer",
      data: rows.map(([t, v]) => ({ name: t, value: +v.beta.toFixed(3), itemStyle: { color: c.segment[v.segment], opacity: opacityFor(t, f), borderRadius: [0, 4, 4, 0], ...border(t, f) } })),
      markLine: { symbol: "none", lineStyle: { color: c.accent, type: "dashed" }, label: { color: c.accent, formatter: "XLE {c}", ...mono }, data: [{ xAxis: +d.returns.betas.benchmarks.XLE.beta.toFixed(2) }] },
    }],
  };
}

export function drawdownOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  const shocks = Object.keys(d.returns.drawdowns);
  return {
    tooltip: {
      trigger: "item",
      formatter: (p: { seriesName: string; name: string; value: number; dataIndex: number }) => {
        const key = Object.keys(SEGMENT_LABELS).find((k) => SEGMENT_LABELS[k as Segment] === p.seriesName) ?? p.seriesName;
        const dd = d.returns.drawdowns[shocks[p.dataIndex]][key];
        return `<b>${p.seriesName}</b> · ${shocks[p.dataIndex]}<br/>${p.value.toFixed(1)}% · peak ${dd.peak} → trough ${dd.trough}`;
      },
    },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
    grid: { bottom: 40 },
    xAxis: { type: "category", data: shocks.map((s) => s.replace(/ (oil bust|COVID crash|rate shock)/, "")) },
    yAxis: pctAxis,
    series: [
      ...segs.map((s) => ({ name: SEGMENT_LABELS[s], type: "bar", itemStyle: { color: c.segment[s] }, data: shocks.map((k) => +(d.returns.drawdowns[k][s].max_drawdown * 100).toFixed(1)) })),
      { name: "XLE", type: "bar", itemStyle: { color: c.text }, data: shocks.map((k) => +(d.returns.drawdowns[k].XLE.max_drawdown * 100).toFixed(1)) },
    ],
  };
}

export function rangeReturnsOption(d: AllData, segs: Segment[], range: [string, string] | null, f: Focus): EChartsCoreOption {
  const idx = rangeIdx(d.ts, range);
  const rows = companiesIn(d, segs)
    .map((t) => [t, rangeReturn(d.ts.symbols[t], idx)] as const)
    .filter((r): r is readonly [string, number] => r[1] != null)
    .sort((a, b) => a[1] - b[1]);
  const xle = rangeReturn(d.ts.symbols.XLE, idx);
  return {
    tooltip: { trigger: "item", valueFormatter: fmtPct },
    xAxis: pctAxis,
    yAxis: { type: "category", data: rows.map(([t]) => t), axisLabel: { ...mono, interval: 0 } },
    series: [{
      type: "bar", barMaxWidth: 14, cursor: "pointer",
      data: rows.map(([t, v]) => ({ name: t, value: +(v * 100).toFixed(1), itemStyle: { color: c.segment[d.returns.betas.companies[t].segment], opacity: opacityFor(t, f), ...border(t, f) } })),
      markLine: xle == null ? undefined : { symbol: "none", lineStyle: { color: c.accent, type: "dashed" }, label: { color: c.accent, formatter: `XLE ${(xle * 100).toFixed(0)}%`, ...mono }, data: [{ xAxis: +(xle * 100).toFixed(1) }] },
    }],
  };
}

export function companyLinesOption(d: AllData, segs: Segment[], range: [string, string] | null, f: Focus): EChartsCoreOption {
  const [i0] = rangeIdx(d.ts, range);
  const rebased = (s: (number | null)[]) => {
    const base = s.slice(i0).find((v) => v != null) ?? null;
    return s.map((v, i) => (i < i0 || v == null || !base ? null : +((v / base) * 100).toFixed(2)));
  };
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "cross", label: { backgroundColor: c.surface2 } }, order: "valueDesc", valueFormatter: (v: unknown) => (v == null ? "n/a" : Number(v).toFixed(1)) },
    grid: { top: 16, bottom: 56 },
    xAxis: { type: "category", data: d.ts.dates, boundaryGap: false, axisLabel: { ...mono, hideOverlap: true } },
    yAxis: { type: "log", logBase: 10, axisLabel: { ...mono }, min: "dataMin" },
    dataZoom: [{ type: "inside", startValue: range?.[0], endValue: range?.[1] }, { type: "slider", height: 24, bottom: 8, startValue: range?.[0], endValue: range?.[1], borderColor: c.border, handleStyle: { color: c.accent }, textStyle: { color: c.textMuted, ...mono } }],
    series: companiesIn(d, segs).map((t) => {
      const seg = d.returns.betas.companies[t].segment;
      const on = t === f.company;
      return { name: t, type: "line", showSymbol: false, data: rebased(d.ts.symbols[t]), z: on ? 5 : 2, lineStyle: { color: on ? c.accent : c.segment[seg], width: on ? 2.6 : 1.1, opacity: opacityFor(t, f) }, itemStyle: { color: on ? c.accent : c.segment[seg] }, emphasis: { focus: "series" } };
    }),
  };
}

export function heatmapOption(d: AllData, segs: Segment[], f: Focus): EChartsCoreOption {
  const comp = d.fundamentals.companies;
  const order = Object.keys(comp).filter((t) => segs.includes(comp[t].segment)).reverse();
  const data = order.flatMap((t, i) =>
    RATIOS.map((r, j) => ({
      name: t,
      value: [j, i, comp[t].segment_percentile[r] ?? -1],
      raw: comp[t][r],
      itemStyle: { opacity: opacityFor(t, f), ...(t === f.company ? { borderColor: c.accent, borderWidth: 2 } : { borderColor: c.bg, borderWidth: 2 }) },
    })),
  );
  return {
    tooltip: {
      formatter: (p: { data: { value: [number, number, number]; raw: number | null } }) => {
        const [j, i, v] = p.data.value;
        const t = order[i];
        return `<b>${t}</b> · ${SEGMENT_LABELS[comp[t].segment]}<br/>${RATIO_LABELS[RATIOS[j]]}: ${pct(p.data.raw)}<br/>Segment median ${pct(d.fundamentals.segment_median[comp[t].segment][RATIOS[j]])}<br/>Percentile in segment: ${(v as number) < 0 ? "n/a (non-standard tag)" : pct(v as number, 0)}<br/>FY end ${comp[t].fiscal_year_end}`;
      },
    },
    grid: { top: 8, bottom: 56, left: 8, right: 8, containLabel: true },
    xAxis: { type: "category", data: RATIOS.map((r) => RATIO_LABELS[r]), axisLabel: { interval: 0, fontSize: 11, color: c.textMuted }, position: "top" },
    yAxis: { type: "category", data: order, axisLabel: { ...mono, interval: 0 } },
    visualMap: { min: 0, max: 1, show: true, orient: "horizontal", left: "center", bottom: 0, itemHeight: 140, calculable: false, text: ["top of segment", "bottom"], textStyle: { color: c.textMuted }, inRange: { color: [c.surface2, c.accent] }, outOfRange: { color: c.grid } },
    series: [{
      type: "heatmap", data, cursor: "pointer",
      label: { show: true, color: c.text, fontFamily: tokens.font.mono, fontSize: 11, formatter: (p: { data: { raw: number | null } }) => (p.data.raw == null ? "n/a" : `${(p.data.raw * 100).toFixed(0)}%`) },
    }],
  };
}

const CLUSTER_SYMBOLS = ["circle", "rect", "triangle", "diamond", "pin"];

export function clusterOption(d: AllData, segs: Segment[], f: Focus): EChartsCoreOption {
  const cl = d.clustering;
  const ev = cl.pca.explained_variance_ratio;
  return {
    tooltip: {
      formatter: (p: { data: { name: string } }) => {
        const t = p.data.name;
        return `<b>${t}</b> · ${SEGMENT_LABELS[cl.pca.segment[t]]}<br/>k-means cluster ${cl.k5.kmeans.assignments[t] + 1} · Ward cluster ${cl.k5.ward.assignments[t] + 1}`;
      },
    },
    grid: { top: 16, bottom: 32 },
    xAxis: { type: "value", name: `PC1 (${(ev[0] * 100).toFixed(0)}%)`, nameLocation: "middle", nameGap: 24, nameTextStyle: { color: c.textMuted }, axisLabel: { ...mono } },
    yAxis: { type: "value", name: `PC2 (${(ev[1] * 100).toFixed(0)}%)`, nameTextStyle: { color: c.textMuted }, axisLabel: { ...mono } },
    series: [{
      type: "scatter", cursor: "pointer",
      data: Object.entries(cl.pca.coords)
        .filter(([t]) => segs.includes(cl.pca.segment[t]))
        .map(([t, [x, y]]) => ({
          name: t, value: [x, y],
          symbol: CLUSTER_SYMBOLS[cl.k5.kmeans.assignments[t] % CLUSTER_SYMBOLS.length],
          symbolSize: t === f.company ? 22 : 15,
          itemStyle: { color: c.segment[cl.pca.segment[t]], opacity: opacityFor(t, f), ...border(t, f) },
          label: { show: true, formatter: t, position: "right", color: c.text, fontFamily: tokens.font.mono, fontSize: 11, opacity: opacityFor(t, f) },
        })),
    }],
  };
}

export function silhouetteOption(d: AllData): EChartsCoreOption {
  const ks = Object.keys(d.clustering.silhouette_by_k.kmeans);
  return {
    tooltip: { trigger: "axis", valueFormatter: (v: unknown) => Number(v).toFixed(3) },
    legend: { bottom: 0, itemWidth: 14, itemHeight: 2 },
    grid: { bottom: 40 },
    xAxis: { type: "category", data: ks, name: "k", nameTextStyle: { color: c.textMuted } },
    yAxis: { type: "value", axisLabel: { ...mono } },
    series: [
      { name: "k-means", type: "line", data: ks.map((k) => d.clustering.silhouette_by_k.kmeans[k]), lineStyle: { color: c.accent, width: 2 }, itemStyle: { color: c.accent }, symbolSize: 8 },
      { name: "Ward", type: "line", data: ks.map((k) => d.clustering.silhouette_by_k.ward[k]), lineStyle: { color: c.segment.majors, type: "dashed" }, itemStyle: { color: c.segment.majors }, symbolSize: 6 },
      { name: "True segments", type: "line", data: ks.map(() => d.clustering.silhouette_of_true_segments), lineStyle: { color: c.danger, type: "dotted" }, itemStyle: { color: c.danger }, symbol: "none" },
    ],
  };
}

export function factorHeatOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  const fs = d.factor.factors;
  const data = segs.flatMap((s, i) => fs.map((fac, j) => [j, i, +d.factor.full_sample[s].t_hac[fac].toFixed(2)]));
  return {
    tooltip: {
      formatter: (p: { value: [number, number, number] }) => {
        const [j, i, t] = p.value;
        const s = segs[i];
        return `<b>${SEGMENT_LABELS[s]}</b> · ${fs[j]}<br/>coef ${d.factor.full_sample[s].coef[fs[j]].toFixed(3)} · HAC t ${t.toFixed(1)}`;
      },
    },
    grid: { top: 8, bottom: 56, containLabel: true },
    xAxis: { type: "category", data: fs, axisLabel: { ...mono, interval: 0 }, position: "top" },
    yAxis: { type: "category", data: segs.map((s) => SEGMENT_LABELS[s]) },
    visualMap: { min: -6, max: 6, orient: "horizontal", left: "center", bottom: 0, itemHeight: 140, text: ["t = +6", "−6"], textStyle: { color: c.textMuted }, inRange: { color: [c.danger, c.surface2, c.accent] } },
    series: [{ type: "heatmap", data, itemStyle: { borderColor: c.bg, borderWidth: 2 }, label: { show: true, color: c.text, fontFamily: tokens.font.mono, fontSize: 11 } }],
  };
}

export function oosOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  return {
    tooltip: { trigger: "axis", valueFormatter: fmtPct },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
    grid: { bottom: 40 },
    xAxis: { type: "category", data: segs.map((s) => SEGMENT_LABELS[s]) },
    yAxis: pctAxis,
    series: [
      { name: "Same-week factors", type: "bar", itemStyle: { color: c.accent }, data: segs.map((s) => +(d.factor.walk_forward_explanatory[s].vs_hist_mean * 100).toFixed(1)) },
      { name: "Last week's factors", type: "bar", itemStyle: { color: c.danger }, data: segs.map((s) => +(d.factor.walk_forward_predictive_lag1[s].vs_hist_mean * 100).toFixed(1)) },
    ],
  };
}

export function scenarioOption(d: AllData, segs: Segment[], move: number): EChartsCoreOption {
  const sc = scenarioAt(d.scenarios, move);
  const cats = segs.map((s) => SEGMENT_LABELS[s]);
  return {
    tooltip: {
      trigger: "axis",
      formatter: (ps: Array<{ dataIndex: number }>) => {
        const s = segs[ps[0].dataIndex];
        const v = sc[s];
        return `<b>${SEGMENT_LABELS[s]}</b> if WTI ${move >= 0 ? "+" : ""}${move}%<br/>expected ${v.expected.toFixed(1)}%<br/>95% band (beta SE) ${v.lo.toFixed(1)}% to ${v.hi.toFixed(1)}%<br/>typical week ${v.predLo.toFixed(1)}% to ${v.predHi.toFixed(1)}%`;
      },
    },
    grid: { top: 16, bottom: 8 },
    xAxis: { type: "category", data: cats },
    yAxis: { ...pctAxis, min: -20, max: 20 },
    series: [
      { type: "bar", barMaxWidth: 44, data: segs.map((s) => ({ value: +sc[s].expected.toFixed(2), itemStyle: { color: c.segment[s], borderRadius: 4 } })) },
      {
        type: "custom",
        renderItem: (_: unknown, api: { value: (i: number) => number; coord: (v: [number, number]) => [number, number]; size: (v: [number, number]) => [number, number] }) => {
          const x = api.value(0);
          const lo = api.coord([x, api.value(1)]);
          const hi = api.coord([x, api.value(2)]);
          const w = api.size([1, 0])[0] * 0.18;
          const style = { stroke: c.text, lineWidth: 1.5 };
          return { type: "group", children: [
            { type: "line", shape: { x1: lo[0], y1: lo[1], x2: hi[0], y2: hi[1] }, style },
            { type: "line", shape: { x1: lo[0] - w, y1: lo[1], x2: lo[0] + w, y2: lo[1] }, style },
            { type: "line", shape: { x1: hi[0] - w, y1: hi[1], x2: hi[0] + w, y2: hi[1] }, style },
          ] };
        },
        encode: { x: 0, y: [1, 2] },
        data: segs.map((s, i) => [i, sc[s].lo, sc[s].hi]),
        z: 5,
      },
    ],
  };
}

export function sizingOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  const years = Object.keys(d.sizing.segment_revenue_usd.majors);
  return {
    tooltip: { trigger: "axis", valueFormatter: (v: unknown) => `$${Number(v).toFixed(0)}bn` },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
    grid: { bottom: 40 },
    xAxis: { type: "category", data: years },
    yAxis: { type: "value", axisLabel: { formatter: "${value}bn", ...mono } },
    series: segs.map((s) => ({ name: SEGMENT_LABELS[s], type: "bar", stack: "rev", itemStyle: { color: c.segment[s] }, data: years.map((y) => +((d.sizing.segment_revenue_usd[s][y] ?? 0) / 1e9).toFixed(1)) })),
  };
}
