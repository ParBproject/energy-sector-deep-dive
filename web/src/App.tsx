import { AnimatePresence, m, useReducedMotion } from "framer-motion";
import { lazy, startTransition, Suspense, useEffect, useRef, useState } from "react";
import { CompanyPanel } from "./components/CompanyPanel";
import { FilterBar } from "./components/FilterBar";
import { loadAll } from "./data/load";
import { tokens } from "./design/tokens";
import { VIEW_LABELS } from "./format";
import { Clusters, Factors, FundamentalsView, Loading, Overview, Returns, Scenario } from "./routes/Views";
const Styleguide = lazy(() => import("./routes/Styleguide").then((m) => ({ default: m.Styleguide })));
import { startUrlSync, urlStateOf, useStore } from "./state/store";
import { serialize, VIEWS, type View } from "./state/url";

const VIEW_COMPONENTS = { overview: Overview, returns: Returns, fundamentals: FundamentalsView, clusters: Clusters, factors: Factors, scenario: Scenario };

function Nav() {
  const st = useStore();
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    ref.current?.querySelector('[aria-current="page"]')?.scrollIntoView({ block: "nearest", inline: "center" });
  }, [st.view]);
  return (
    <nav className="views" aria-label="Views" ref={ref}>
      {VIEWS.map((v) => (
        <a key={v} href={serialize({ ...urlStateOf(st), view: v })} aria-current={st.view === v ? "page" : undefined}>
          {VIEW_LABELS[v]}
        </a>
      ))}
    </nav>
  );
}

/** Horizontal swipe on mobile moves to the previous/next view (not when gesturing on a chart). */
function useSwipe(el: React.RefObject<HTMLElement | null>, view: View, setView: (v: View) => void) {
  useEffect(() => {
    const node = el.current;
    if (!node) return;
    let x0 = 0, y0 = 0, active = false;
    const start = (e: TouchEvent) => {
      active = !(e.target as HTMLElement).closest(".chart, input, .panel");
      x0 = e.touches[0].clientX;
      y0 = e.touches[0].clientY;
    };
    const end = (e: TouchEvent) => {
      if (!active) return;
      const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
      if (Math.abs(dx) < 70 || Math.abs(dy) > Math.abs(dx) * 0.6) return;
      const i = VIEWS.indexOf(view as (typeof VIEWS)[number]);
      const next = VIEWS[Math.min(VIEWS.length - 1, Math.max(0, i + (dx < 0 ? 1 : -1)))];
      if (next !== view) setView(next);
    };
    node.addEventListener("touchstart", start, { passive: true });
    node.addEventListener("touchend", end, { passive: true });
    return () => {
      node.removeEventListener("touchstart", start);
      node.removeEventListener("touchend", end);
    };
  }, [el, view, setView]);
}

export function App() {
  const { data, error, view, setView, setData, setError } = useStore();
  const reduced = useReducedMotion();
  /** Mount the chart-heavy views in a transition so React can yield (keeps long tasks short). */
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (data) startTransition(() => setReady(true));
  }, [data]);
  const main = useRef<HTMLElement>(null);
  useEffect(() => startUrlSync(), []);
  useEffect(() => {
    loadAll().then(setData).catch((e: Error) => setError(e.message));
  }, [setData, setError]);
  useSwipe(main, view, setView);
  useEffect(() => {
    document.title = `${view === "styleguide" ? "Styleguide" : VIEW_LABELS[view]} · Energy Sector Explorer`;
  }, [view]);

  if (view === "styleguide") return <Suspense fallback={null}><Styleguide /></Suspense>;
  const ViewC = VIEW_COMPONENTS[view];
  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="container topbar">
        <h1 className="brand">
          Energy Sector Explorer
          <small>US oil &amp; gas segments vs WTI, XLE and the S&amp;P 500 · 2015 to date</small>
        </h1>
        <div className="top-links only-desktop">
          <a className="btn linkbtn" href="https://github.com/ParBproject/energy-sector-deep-dive">Code &amp; method</a>
          <a className="btn linkbtn" href="#/styleguide">Styleguide</a>
        </div>
      </header>
      <FilterBar asOf={data?.index.as_of} />
      <div className="container"><Nav /></div>
      <main id="main" className="container" ref={main}>
        {error && <p role="alert">Could not load data: {error}</p>}
        <AnimatePresence mode="wait" initial={false}>
          <m.section
            key={view}
            aria-label={VIEW_LABELS[view]}
            initial={reduced ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduced ? { opacity: 1 } : { opacity: 0, y: -6 }}
            transition={{ duration: reduced ? 0 : tokens.motion.fast }}
          >
            {data && ready ? <ViewC d={data} /> : <Loading title={VIEW_LABELS[view]} view={view} />}
          </m.section>
        </AnimatePresence>
        <footer className="foot">
          Sensitivity analysis and descriptive statistics only; nothing here is a trading signal. Data: yfinance, FRED, SEC EDGAR, Fama-French, U.S. EIA; snapshot {data?.index.snapshot_built_at.slice(0, 10) ?? "…"}, EIA data as of {data?.eia.as_of ?? "…"}.
        </footer>
      </main>
      <CompanyPanel />
    </>
  );
}
