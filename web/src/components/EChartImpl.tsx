import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, CustomChart, HeatmapChart, LineChart, ScatterChart } from "echarts/charts";
import { AriaComponent, DataZoomComponent, GridComponent, LegendComponent, MarkLineComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
import { echartsTheme, THEME_NAME } from "../design/echartsTheme";
import { usePrefersReducedMotion } from "./useReducedMotion";

echarts.use([AriaComponent, BarChart, LineChart, ScatterChart, HeatmapChart, CustomChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, VisualMapComponent, DataZoomComponent, CanvasRenderer]);
echarts.registerTheme(THEME_NAME, echartsTheme);

export interface Props {
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

function apply(ch: echarts.ECharts, option: EChartsCoreOption, reduced: boolean) {
  ch.setOption({ aria: { enabled: true }, animation: !reduced, animationDuration: 450, animationDurationUpdate: 450, ...option }, { notMerge: false, replaceMerge: ["series"] });
}

export default function EChartImpl({ option, label, onPick, onRange, group, height }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const handlers = useRef({ onPick, onRange });
  handlers.current = { onPick, onRange };
  const reduced = usePrefersReducedMotion();

  const latest = useRef({ option, reduced });
  latest.current = { option, reduced };

  useEffect(() => {
    if (!ref.current) return;
    const node = ref.current;
    let ch: echarts.ECharts | null = null;
    let t: ReturnType<typeof setTimeout> | undefined;
    let ro: ResizeObserver | null = null;
    // Initialise each chart in its own macrotask so several charts don't form one long main-thread task.
    const boot = setTimeout(() => {
    ch = echarts.init(node, THEME_NAME, { renderer: "canvas" });
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
    ch.on("datazoom", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        const opt = ch!.getOption() as { dataZoom?: Array<{ startValue?: number; endValue?: number; start?: number; end?: number }>; xAxis?: Array<{ data?: string[] }> };
        const dz = opt.dataZoom?.[0];
        const cats = opt.xAxis?.[0]?.data;
        if (!dz || !cats) return;
        const full = (dz.start ?? 0) <= 0.01 && (dz.end ?? 100) >= 99.99;
        handlers.current.onRange?.(full ? null : [cats[dz.startValue ?? 0], cats[dz.endValue ?? cats.length - 1]]);
      }, 250);
    });
    apply(ch, latest.current.option, latest.current.reduced);
    ro = new ResizeObserver(() => ch?.resize());
    ro.observe(node);
    }, 0);
    return () => {
      clearTimeout(boot);
      clearTimeout(t);
      ro?.disconnect();
      ch?.dispose();
      chart.current = null;
    };
  }, [group]);

  useEffect(() => {
    if (chart.current) apply(chart.current, option, reduced);
  }, [option, reduced]);

  return <div ref={ref} className="chart" style={height ? { height, flex: "none" } : undefined} role="img" aria-label={label} tabIndex={0} />;
}
