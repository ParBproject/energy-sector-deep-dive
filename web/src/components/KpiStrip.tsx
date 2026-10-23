import type { AllData } from "../data/types";
import { SEGMENT_LABELS, pct, usdBn } from "../format";

export function KpiStrip({ data }: { data: AllData | null }) {
  const items = data
    ? [
        {
          label: "Highest oil beta",
          value: data.returns.betas.segments[data.returns.highest_beta_segment].beta.toFixed(2),
          sub: `${SEGMENT_LABELS[data.returns.highest_beta_segment]} · per 1% WTI`,
        },
        {
          label: `FY${data.sizing.latest_fiscal_year} revenue`,
          value: usdBn(data.sizing.total_revenue_latest_usd),
          sub: "18-name universe, 10-K",
        },
        {
          label: "Clusters vs segments",
          value: data.clustering.k5.kmeans.adjusted_rand_vs_segments.toFixed(2),
          sub: "Adjusted Rand index, k=5",
        },
        {
          label: "Forecast OOS R²",
          value: pct(Math.max(...Object.values(data.factor.walk_forward_predictive_lag1).map((v) => v.vs_hist_mean))),
          sub: "Best segment, lag-1 factors",
        },
      ]
    : Array.from({ length: 4 }, () => null);
  return (
    <section className="kpis grid12" aria-label="Key figures">
      {items.map((k, i) => (
        <div className="kpi span-3" key={i}>
          {k ? (
            <>
              <div className="label">{k.label}</div>
              <div className="value num">{k.value}</div>
              <div className="sub">{k.sub}</div>
            </>
          ) : (
            <div className="skeleton" style={{ minHeight: 72 }} role="status" aria-label="Loading figure" />
          )}
        </div>
      ))}
    </section>
  );
}
