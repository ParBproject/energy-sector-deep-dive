import * as echarts from "echarts/core";
import { tokens } from "./tokens";

const c = tokens.color;
export const THEME_NAME = "energy";

export const echartsTheme = {
  color: [c.accent, ...Object.values(c.segment)],
  backgroundColor: "transparent",
  textStyle: { fontFamily: tokens.font.ui, color: c.text, fontSize: tokens.font.size.xs },
  title: { textStyle: { color: c.text } },
  legend: { textStyle: { color: c.textMuted }, inactiveColor: c.border },
  tooltip: {
    backgroundColor: c.surface2,
    borderColor: c.border,
    textStyle: { color: c.text, fontFamily: tokens.font.mono, fontSize: tokens.font.size.xs },
  },
  grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
  categoryAxis: {
    axisLine: { lineStyle: { color: c.border } },
    axisTick: { show: false },
    axisLabel: { color: c.textMuted },
    splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false },
    axisLabel: { color: c.textMuted, fontFamily: tokens.font.mono },
    splitLine: { lineStyle: { color: c.grid } },
  },
  line: { symbol: "none", lineStyle: { width: 2 } },
};

export function registerTheme(): void {
  echarts.registerTheme(THEME_NAME, echartsTheme);
}
