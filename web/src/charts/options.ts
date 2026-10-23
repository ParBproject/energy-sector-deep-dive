import type { EChartsCoreOption } from "echarts/core";
import { tokens, type Segment } from "../design/tokens";
import type { AllData } from "../data/types";
import { SEGMENT_LABELS } from "../format";

const c = tokens.color;
const mono = { fontFamily: tokens.font.mono };

export function oilBetaOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  const rows = Object.entries(d.returns.betas.companies)
    .filter(([, v]) => segs.includes(v.segment))
    .sort((a, b) => a[1].beta - b[1].beta);
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: rows.map(([t]) => t), axisLabel: { ...mono, interval: 0 } },
    series: [
      {
        type: "bar",
        data: rows.map(([, v]) => ({ value: +v.beta.toFixed(3), itemStyle: { color: c.segment[v.segment], borderRadius: [0, 4, 4, 0] } })),
        barMaxWidth: 14,
        markLine: {
          symbol: "none",
          lineStyle: { color: c.accent, type: "dashed" },
          label: { color: c.accent, formatter: "XLE {c}", ...mono },
          data: [{ xAxis: +d.returns.betas.benchmarks.XLE.beta.toFixed(2) }],
        },
      },
    ],
  };
}

export function drawdownOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  const shocks = Object.keys(d.returns.drawdowns);
  return {
    tooltip: { trigger: "axis", valueFormatter: (v: unknown) => `${Number(v).toFixed(1)}%` },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
    grid: { bottom: 40 },
    xAxis: { type: "category", data: shocks.map((s) => s.replace(/ (oil bust|COVID crash|rate shock)/, "")) },
    yAxis: { type: "value", axisLabel: { formatter: "{value}%", ...mono } },
    series: segs.map((s) => ({
      name: SEGMENT_LABELS[s],
      type: "bar",
      itemStyle: { color: c.segment[s] },
      data: shocks.map((k) => +(d.returns.drawdowns[k][s].max_drawdown * 100).toFixed(1)),
    })),
  };
}

export function scenarioOption(d: AllData, segs: Segment[], move: number): EChartsCoreOption {
  const grid = Object.keys(d.scenarios.grid).map(Number).sort((a, b) => a - b);
  return {
    tooltip: { trigger: "axis", valueFormatter: (v: unknown) => `${Number(v).toFixed(1)}%` },
    legend: { bottom: 0, itemWidth: 14, itemHeight: 2 },
    grid: { bottom: 40 },
    xAxis: { type: "value", min: -30, max: 30, axisLabel: { formatter: "{value}%", ...mono } },
    yAxis: { type: "value", axisLabel: { formatter: "{value}%", ...mono } },
    series: [
      ...segs.map((s) => ({
        name: SEGMENT_LABELS[s],
        type: "line",
        lineStyle: { color: c.segment[s], width: 2 },
        itemStyle: { color: c.segment[s] },
        data: grid.map((g) => [g, +d.scenarios.grid[String(g)][s].expected_pct.toFixed(2)]),
      })),
      {
        name: "WTI move",
        type: "line",
        data: [],
        markLine: { symbol: "none", lineStyle: { color: c.accent, width: 2 }, label: { color: c.accent, formatter: `WTI ${move}%`, ...mono }, data: [{ xAxis: move }] },
      },
    ],
  };
}

export function oosOption(d: AllData, segs: Segment[]): EChartsCoreOption {
  return {
    tooltip: { trigger: "axis", valueFormatter: (v: unknown) => `${Number(v).toFixed(1)}%` },
    legend: { bottom: 0, itemWidth: 10, itemHeight: 10 },
    grid: { bottom: 40 },
    xAxis: { type: "category", data: segs.map((s) => SEGMENT_LABELS[s]) },
    yAxis: { type: "value", axisLabel: { formatter: "{value}%", ...mono } },
    series: [
      { name: "Same-week factors", type: "bar", itemStyle: { color: c.accent }, data: segs.map((s) => +(d.factor.walk_forward_explanatory[s].vs_hist_mean * 100).toFixed(1)) },
      { name: "Last week's factors", type: "bar", itemStyle: { color: c.danger }, data: segs.map((s) => +(d.factor.walk_forward_predictive_lag1[s].vs_hist_mean * 100).toFixed(1)) },
    ],
  };
}
