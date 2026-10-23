import { lazy, Suspense } from "react";
import type { Props } from "./EChartImpl";

/** ECharts (~1 MB) is split into its own chunk and loaded after first paint. */
const Impl = lazy(() => import("./EChartImpl"));

export function EChart(props: Props) {
  const fallback = <div className="chart skeleton-chart" style={props.height ? { height: props.height, flex: "none" } : undefined} role="img" aria-label={`${props.label} (loading)`} />;
  return (
    <Suspense fallback={fallback}>
      <Impl {...props} />
    </Suspense>
  );
}
