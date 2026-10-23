import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, CustomChart, HeatmapChart, LineChart, ScatterChart } from "echarts/charts";
import { DataZoomComponent, GridComponent, LegendComponent, MarkLineComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
import { THEME_NAME } from "../design/echartsTheme";
import { usePrefersReducedMotion } from "./useReducedMotion";

echarts.use([BarChart, LineChart, ScatterChart, HeatmapChart, CustomChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, VisualMapComponent, DataZoomComponent, CanvasRenderer]);

interface Props {
  option: EChartsCoreOption;
  label: string;
  /** Called with the data item name (a ticker) when a mark is clicked/tapped. */
  onPick?: (name: string) => void;
  /** Called with the [start, end] category values after a zoom/brush settles. */
  onRange?: (range: [string, string] | null) => void;
  /** Charts in the same group share a synced crosshair. */
  group?: string;
  height?: number;
}

export function EChart({ option, label, onPick, onRange, group, height }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const handlers = useRef({ onPick, onRange });
  handlers.current = { onPick, onRange };
  const reduced = usePrefersReducedMotion();

  useEffect(() => {
    if (!ref.current) return;
    const ch = echarts.init(ref.current, THEME_NAME, { renderer: "canvas" });
    chart.current = ch;
    if (group) {
      ch.group = group;
      echarts.connect(group);
    }
    ch.on("click", (p) => {
      const data = p.data as { name?: string } | null | undefined;
      const n = (data && typeof data === "object" ? data.name : undefined) ?? p.name;
      if (n) handlers.current.onPick?.(n);
    });
    let t: ReturnType<typeof setTimeout> | undefined;
    ch.on("datazoom", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        const opt = ch.getOption() as { dataZoom?: Array<{ startValue?: number; endValue?: number; start?: number; end?: number }>; xAxis?: Array<{ data?: string[] }> };
        const dz = opt.dataZoom?.[0];
        const cats = opt.xAxis?.[0]?.data;
        if (!dz || !cats) return;
        const full = (dz.start ?? 0) <= 0.01 && (dz.end ?? 100) >= 99.99;
        handlers.current.onRange?.(full ? null : [cats[dz.startValue ?? 0], cats[dz.endValue ?? cats.length - 1]]);
      }, 250);
    });
    const ro = new ResizeObserver(() => ch.resize());
    ro.observe(ref.current);
    return () => {
      clearTimeout(t);
      ro.disconnect();
      ch.dispose();
    };
  }, [group]);

  useEffect(() => {
    chart.current?.setOption({ animation: !reduced, animationDuration: 450, animationDurationUpdate: 450, ...option }, { notMerge: false, replaceMerge: ["series"] });
  }, [option, reduced]);

  return <div ref={ref} className="chart" style={height ? { height, flex: "none" } : undefined} role="img" aria-label={label} />;
}
