import { useEffect, useMemo, useRef } from "react";
import { ChartCard } from "../components/ChartCard";
import { EChart } from "../components/EChart";
import { FilterBar } from "../components/FilterBar";
import { KpiStrip } from "../components/KpiStrip";
import { drawdownOption, oilBetaOption, oosOption, scenarioOption } from "../charts/options";
import { SEGMENT_LABELS, signed } from "../format";
import { useStore } from "../state/store";

const CARDS = [
  { id: "beta", tab: "Oil beta" },
  { id: "drawdowns", tab: "Drawdowns" },
  { id: "scenario", tab: "Scenario" },
  { id: "oos", tab: "Forecastability" },
];

export function Shell() {
  const { data, error, segments, oilMove, setOilMove, tab, setTab } = useStore();
  const track = useRef<HTMLDivElement>(null);
  const opts = useMemo(
    () =>
      data && {
        beta: oilBetaOption(data, segments),
        drawdowns: drawdownOption(data, segments),
        scenario: scenarioOption(data, segments, oilMove),
        oos: oosOption(data, segments),
      },
    [data, segments, oilMove],
  );
  const asOf = data?.index.as_of;
  const src = data?.index.sources ?? {};

  // swipe: keep tab state in sync with the scroll-snap position
  useEffect(() => {
    const el = track.current;
    if (!el) return;
    const on = () => {
      const i = Math.round(el.scrollLeft / el.clientWidth);
      if (i !== useStore.getState().tab) setTab(i);
    };
    el.addEventListener("scroll", on, { passive: true });
    return () => el.removeEventListener("scroll", on);
  }, [setTab]);

  const goTab = (i: number) => {
    setTab(i);
    const el = track.current;
    el?.scrollTo({ left: i * el.clientWidth, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  };

  const upstreamAtMove = data?.scenarios.grid[String(Math.round(oilMove / 5) * 5)]?.upstream;

  return (
    <>
      <header className="container topbar">
        <h1 className="brand">
          Energy Sector Explorer
          <small>US oil &amp; gas segments vs WTI, XLE and the S&amp;P 500 · 2015 to date</small>
        </h1>
        <a className="btn linkbtn only-desktop" href="#/styleguide">
          Styleguide
        </a>
      </header>
      <FilterBar asOf={asOf} />
      <main className="container">
        {error && <p role="alert">Could not load data: {error}</p>}
        <KpiStrip data={data} />
        <div className="tabs" role="tablist" aria-label="Charts">
          {CARDS.map((c, i) => (
            <button key={c.id} role="tab" aria-selected={tab === i} aria-controls={c.id} onClick={() => goTab(i)}>
              {c.tab}
            </button>
          ))}
        </div>
        <div className="charts grid12" ref={track}>
          <ChartCard id="beta" title="Oil beta by company" description="Daily return per 1% move in WTI (CL=F), HAC errors." source={src["returns.json"] ?? "…"} asOf={asOf} loading={!opts}>
            {opts && <EChart option={opts.beta} label="Bar chart of oil beta by company" />}
          </ChartCard>
          <ChartCard id="drawdowns" title="Drawdowns in three shocks" description="Equal-weighted segment peak-to-trough within each window." source={src["returns.json"] ?? "…"} asOf={asOf} loading={!opts}>
            {opts && <EChart option={opts.drawdowns} label="Grouped bar chart of segment drawdowns" />}
          </ChartCard>
          <ChartCard id="scenario" title="Oil scenario (sensitivity, not a signal)" description="Expected one-week segment move for a WTI move." source={src["scenarios.json"] ?? "…"} asOf={asOf} loading={!opts}>
            {opts && (
              <>
                <label className="label" htmlFor="oil">
                  WTI move <span className="num">{signed(oilMove, 0)}</span>
                  {upstreamAtMove && (
                    <> · {SEGMENT_LABELS.upstream} <span className="num">{signed(upstreamAtMove.expected_pct)}</span></>
                  )}
                </label>
                <input id="oil" className="slider" type="range" min={-30} max={30} step={5} value={oilMove} onChange={(e) => setOilMove(Number(e.target.value))} />
                <EChart option={opts.scenario} label="Line chart of expected segment move against WTI move" />
              </>
            )}
          </ChartCard>
          <ChartCard id="oos" title="Explains well, forecasts nothing" description="Walk-forward out-of-sample R² vs historical mean." source={src["factor_model.json"] ?? "…"} asOf={data?.factor.sample.last_week} loading={!opts}>
            {opts && <EChart option={opts.oos} label="Bar chart of out-of-sample R squared" />}
          </ChartCard>
        </div>
      </main>
    </>
  );
}
