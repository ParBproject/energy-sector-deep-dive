import { useMemo } from "react";
import { ChartCard } from "../components/ChartCard";
import { EChart } from "../components/EChart";
import { KpiStrip } from "../components/KpiStrip";
import * as O from "../charts/options";
import { scenarioAt } from "../data/derive";
import type { AllData } from "../data/types";
import { tokens, type Segment } from "../design/tokens";
import { SEGMENT_LABELS, eiaStamp, signed, usdBn } from "../format";
import { useStore } from "../state/store";

function useCommon() {
  const st = useStore();
  const focus = useMemo(() => ({ company: st.company, pins: st.pins }), [st.company, st.pins]);
  return { ...st, focus, src: st.data?.index.sources ?? {}, asOf: st.data?.index.as_of };
}

const EIA_CARDS: [string, string][] = [
  ["crude_production_us", "EIA series MCRFPUS2, monthly."],
  ["crude_stocks_us", "EIA series WCESTUS1, weekly."],
  ["rotary_rigs_us", "EIA series E_ERTRRO_XR0_NUS_C (Baker Hughes via EIA), monthly; EIA publishes it with a lag of several months."],
];
const HERO_DESC = "Weekly total-return index (log scale). Drag the handles or pinch to re-scope every view to a date range.";
/** Placeholder with the same card copy as the real view, so the first paint already shows the headline content. */
const Loading = ({ title, view }: { title: string; view?: string }) => (
  <div className="loading-view">
    {view === "overview" ? (
      <div className="grid12 cards"><ChartCard id="ld-hero" span={12} title="Segments vs XLE and the S&P 500" description={HERO_DESC} source="…" loading /></div>
    ) : (
      <ChartCard id={`ld-${title}`} title={title} source="…" loading span={12} />
    )}
  </div>
);

export function Overview({ d }: { d: AllData }) {
  const { segments, range, focus, setRange, selectCompany, src, asOf } = useCommon();
  const hero = useMemo(() => O.heroOption(d, segments, range, focus), [d, segments, range, focus]);
  const beta = useMemo(() => O.oilBetaOption(d, segments, focus), [d, segments, focus]);
  const size = useMemo(() => O.sizingOption(d, segments), [d, segments]);
  const eiaOpts = useMemo(() => EIA_CARDS.map(([n]) => O.eiaLineOption(d, n)), [d]);
  const stamp = eiaStamp(d.eia);
  const td = d.sizing.topdown_status;
  return (
    <>
      <KpiStrip data={d} />
      <div className="grid12 cards">
        <ChartCard id="hero" span={12} title="Segments vs XLE and the S&P 500" description={HERO_DESC} source={src["timeseries.json"]} asOf={asOf}>
          <EChart option={hero} label="Line chart of segment total-return indices" onRange={setRange} group="ts" />
        </ChartCard>
        <ChartCard id="beta" span={6} title="Oil beta by company" description="Daily return per 1% WTI move, 2015 to date. Tap a bar for detail." source={src["returns.json"]} asOf={asOf}>
          <EChart option={beta} label="Bar chart of oil beta by company" onPick={selectCompany} />
        </ChartCard>
        <ChartCard id="sizing" span={6} title="Reported revenue by segment" description={`A bottom-up proxy, not a market size: FY${d.sizing.latest_fiscal_year} total ${usdBn(d.sizing.total_revenue_latest_usd)}. Global revenue, double counts the value chain.`} source={src["market_sizing.json"]} asOf={asOf}>
          <EChart option={size} label="Stacked bar chart of revenue by segment and year" />
        </ChartCard>
        {EIA_CARDS.map(([n, desc], i) => {
          const s = d.eia.series[n];
          const extra = n === "crude_production_us" && td.available ? ` ${td.year} average ${Math.round(td.us_crude_production_avg_kbd!).toLocaleString("en-US")} kb/d, worth ${usdBn(td.us_crude_value_usd!)} at WTI.` : "";
          return (
            <ChartCard key={n} id={`eia-${n}`} span={4} title={s.label} description={`${desc} Latest: ${s.latest_period}, ${s.values[s.values.length - 1].toLocaleString("en-US")} ${s.units}.${extra}`} stamp={stamp}>
              <EChart option={eiaOpts[i]} label={`Line chart of ${s.label}`} />
            </ChartCard>
          );
        })}
      </div>
    </>
  );
}

export function Returns({ d }: { d: AllData }) {
  const { segments, range, focus, setRange, selectCompany, src, asOf } = useCommon();
  const lines = useMemo(() => O.companyLinesOption(d, segments, range, focus), [d, segments, range, focus]);
  const rr = useMemo(() => O.rangeReturnsOption(d, segments, range, focus), [d, segments, range, focus]);
  const dd = useMemo(() => O.drawdownOption(d, segments), [d, segments]);
  return (
    <div className="grid12 cards">
      <ChartCard id="lines" span={8} title="Company total return" description="Rebased to 100 at the start of the selected range. Hover for values, tap a line for detail." source={src["timeseries.json"]} asOf={asOf}>
        <EChart option={lines} label="Line chart of company total-return indices" onRange={setRange} onPick={selectCompany} group="ts" />
      </ChartCard>
      <ChartCard id="rr" span={4} title={range ? `Return ${range[0]} → ${range[1]}` : "Return since 2015"} description="Dashed line: XLE over the same range." source={src["timeseries.json"]} asOf={asOf}>
        <EChart option={rr} label="Bar chart of company returns over the selected range" onPick={selectCompany} />
      </ChartCard>
      <ChartCard id="dd" span={12} title="Drawdowns in three shocks" description="Equal-weighted segment peak-to-trough within each window, with XLE. Hover for peak and trough dates." source={src["returns.json"]} asOf={asOf}>
        <EChart option={dd} label="Grouped bar chart of drawdowns" />
      </ChartCard>
    </div>
  );
}

// heatmap click gives a cell, not a name: resolve via a wrapper
export function FundamentalsView({ d }: { d: AllData }) {
  const { segments, focus, selectCompany, src } = useCommon();
  const order = useMemo(() => Object.keys(d.fundamentals.companies).filter((t) => segments.includes(d.fundamentals.companies[t].segment)).reverse(), [d, segments]);
  const hm = useMemo(() => O.heatmapOption(d, segments, focus), [d, segments, focus]);
  return (
    <div className="grid12 cards">
      <ChartCard id="heat" span={12} title="Point-in-time fundamentals" description="Shade = percentile within the segment; cell text = raw value. Uses only 10-Ks filed by the as-of date. n/a = filed under a non-standard tag, left blank rather than estimated. Tap a row for detail." source={src["fundamentals.json"]} asOf={d.fundamentals.as_of}>
        <EChart option={hm} label="Heatmap of fundamental ratios by company" onPick={selectCompany} height={Math.max(360, 30 * order.length + 100)} />
      </ChartCard>
    </div>
  );
}

export function Clusters({ d }: { d: AllData }) {
  const { segments, focus, selectCompany, src, asOf } = useCommon();
  const sc = useMemo(() => O.clusterOption(d, segments, focus), [d, segments, focus]);
  const sil = useMemo(() => O.silhouetteOption(d), [d]);
  const k = d.clustering.k5.kmeans;
  return (
    <div className="grid12 cards">
      <ChartCard id="pca" span={8} title={`Clusters vs segments · ARI ${k.adjusted_rand_vs_segments.toFixed(2)}`} description={`k-means (k=5) on oil beta + 5 fundamentals, shown in PCA space. Colour = segment, shape = cluster. ${d.clustering.n_imputed_cells} imputed cells (universe median, flagged).`} source={src["clustering.json"]} asOf={asOf}>
        <EChart option={sc} label="Scatter plot of companies in PCA space" onPick={selectCompany} />
      </ChartCard>
      <ChartCard id="sil" span={4} title="Silhouette by k" description="Higher = tighter clusters. The true segments score lower than any clustering on these features." source={src["clustering.json"]} asOf={asOf}>
        <EChart option={sil} label="Line chart of silhouette score by number of clusters" />
      </ChartCard>
    </div>
  );
}

export function Factors({ d }: { d: AllData }) {
  const { segments, src } = useCommon();
  const fh = useMemo(() => O.factorHeatOption(d, segments), [d, segments]);
  const oos = useMemo(() => O.oosOption(d, segments), [d, segments]);
  const s = d.factor.sample;
  return (
    <div className="grid12 cards">
      <ChartCard id="fh" span={7} title="Weekly factor exposures (HAC t-stats)" description={`brent_wti is a crack-spread proxy (${d.factor.crack_spread_proxy.split(";")[0]}). Dollar: ${d.factor.dollar_proxy}.`} source={src["factor_model.json"]} asOf={s.last_week}>
        <EChart option={fh} label="Heatmap of factor t statistics by segment" />
      </ChartCard>
      <ChartCard id="oos" span={5} title="Explains well, forecasts nothing" description={`Walk-forward OOS R² vs historical mean, ${s.n_weeks} weeks. Green: same-week factors. Red: last week's factors.`} source={src["factor_model.json"]} asOf={s.last_week}>
        <EChart option={oos} label="Bar chart of out-of-sample R squared" />
      </ChartCard>
    </div>
  );
}

export function Scenario({ d }: { d: AllData }) {
  const { segments, oil, setOil, oilSource, setOilSource, src, asOf } = useCommon();
  const fc = d.scenarios.forecaster_input;
  const move = oilSource === "forecaster" && fc.implied_move_pct != null ? +fc.implied_move_pct.toFixed(2) : oil;
  const opt = useMemo(() => O.scenarioOption(d, segments, move), [d, segments, move]);
  const sc = scenarioAt(d.scenarios, move);
  return (
    <div className="grid12 cards">
      <ChartCard id="scen" span={8} title="Oil scenario · sensitivity, not a signal" description="Expected one-week move per segment for a WTI move, from weekly oil betas. Whiskers: 95% band from the beta's HAC standard error." source={src["scenarios.json"]} asOf={asOf}>
        <div className="scen-controls">
          <div role="radiogroup" aria-label="Oil move source" className="seg-toggle">
            <button role="radio" aria-checked={oilSource === "slider"} onClick={() => setOilSource("slider")}>Slider</button>
            <button role="radio" aria-checked={oilSource === "forecaster"} disabled={fc.implied_move_pct == null} onClick={() => setOilSource("forecaster")}>Forecaster preset</button>
          </div>
          <label className="label" htmlFor="oil">WTI move <span className="num big">{signed(move, oilSource === "forecaster" ? 2 : 0)}</span></label>
          <input id="oil" className="slider" type="range" min={-30} max={30} step={1} value={Math.round(move)} onChange={(e) => setOil(Number(e.target.value))} aria-valuetext={`${move}%`} />
        </div>
        <EChart option={opt} label="Bar chart of expected segment moves with confidence whiskers" />
      </ChartCard>
      <div className="card span-4 side">
        <h2>Readout</h2>
        <table className="ratios">
          <thead><tr><th>Segment</th><th>Expected</th><th>95% band</th></tr></thead>
          <tbody>
            {segments.map((s: Segment) => (
              <tr key={s}>
                <td><span className="dot" style={{ background: tokens.color.segment[s] }} /> {SEGMENT_LABELS[s]}</td>
                <td className="num">{signed(sc[s].expected, Math.abs(move) < 1 ? 2 : 1)}</td>
                <td className="num">{sc[s].lo.toFixed(Math.abs(move) < 1 ? 2 : 1)} to {sc[s].hi.toFixed(Math.abs(move) < 1 ? 2 : 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3 style={{ marginTop: 16 }}>Forecaster preset</h3>
        {fc.implied_move_pct != null ? (
          <p className="desc">
            commodity-price-forecaster's latest published one-step WTI forecast ({fc.model}, week {fc.target_week}, commit <span className="num">{fc.source_commit?.slice(0, 7)}</span>, vendored {fc.vendored_on}) implied <span className="num">{signed(fc.implied_move_pct, 2)}</span>. WTI actually moved <span className="num">{signed(fc.realized_move_pct ?? 0, 2)}</span>. That step is <strong>already realized</strong>: it is a dated preset, not a forward view.
          </p>
        ) : (
          <p className="desc">No forecaster output vendored; slider only.</p>
        )}
        <p className="desc">{d.scenarios.framing}</p>
      </div>
    </div>
  );
}

export { Loading };
