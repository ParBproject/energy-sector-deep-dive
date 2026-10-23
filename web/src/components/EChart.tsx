import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
import { THEME_NAME } from "../design/echartsTheme";
import { usePrefersReducedMotion } from "./useReducedMotion";

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, CanvasRenderer]);

export function EChart({ option, label }: { option: EChartsCoreOption; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    if (!ref.current) return;
    chart.current = echarts.init(ref.current, THEME_NAME, { renderer: "canvas" });
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(ref.current);
    return () => {
      ro.disconnect();
      chart.current?.dispose();
    };
  }, []);

  useEffect(() => {
    chart.current?.setOption({ animation: !reduced, animationDuration: 400, ...option }, true);
  }, [option, reduced]);

  return <div ref={ref} className="chart" role="img" aria-label={label} />;
}
