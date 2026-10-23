import { AnimatePresence, m, useReducedMotion } from "framer-motion";
import { useEffect, useMemo, useRef } from "react";
import { createPortal } from "react-dom";
import { tokens } from "../design/tokens";
import { rangeIdx, rangeReturn } from "../data/derive";
import { RATIOS } from "../data/types";
import { RATIO_LABELS, SEGMENT_LABELS, pct, usdBn } from "../format";
import { useStore } from "../state/store";
import { EChart } from "./EChart";

const c = tokens.color;

export function CompanyPanel() {
  const { data, company, selectCompany, pins, togglePin, range, onlySegment } = useStore();
  const reduced = useReducedMotion();
  const opener = useRef<HTMLElement | null>(null);
  const open = Boolean(company);
  useEffect(() => {
    const track = (e: FocusEvent) => {
      const t = e.target as HTMLElement;
      if (!t.closest?.(".panel")) opener.current = t;
    };
    document.addEventListener("focusin", track);
    return () => document.removeEventListener("focusin", track);
  }, []);
  useEffect(() => {
    if (!open && opener.current?.isConnected) opener.current.focus();
  }, [open]);
  /** Keep Tab inside the dialog while it is open. */
  const trap = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") return selectCompany(null);
    if (e.key !== "Tab") return;
    const f = e.currentTarget.querySelectorAll<HTMLElement>("button, [href], [tabindex]:not([tabindex='-1'])");
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };
  const info = data && company ? data.returns.betas.companies[company] : null;
  const fund = data && company ? data.fundamentals.companies[company] : null;
  const option = useMemo(() => {
    if (!data || !company || !info) return null;
    const [i0, i1] = rangeIdx(data.ts, range);
    const dates = data.ts.dates.slice(i0, i1 + 1);
    const rebase = (s: (number | null)[]) => {
      const part = s.slice(i0, i1 + 1);
      const b = part.find((v) => v != null);
      return part.map((v) => (v == null || !b ? null : +((v / b) * 100).toFixed(1)));
    };
    const seg = info.segment;
    return {
      tooltip: { trigger: "axis", valueFormatter: (v: unknown) => (v == null ? "n/a" : Number(v).toFixed(1)) },
      legend: { bottom: 0, itemWidth: 14, itemHeight: 2 },
      grid: { top: 12, bottom: 36, left: 4, right: 8 },
      xAxis: { type: "category", data: dates, boundaryGap: false, axisLabel: { hideOverlap: true, fontFamily: tokens.font.mono } },
      yAxis: { type: "value", scale: true, axisLabel: { fontFamily: tokens.font.mono } },
      series: [
        { name: company, type: "line", showSymbol: false, data: rebase(data.ts.symbols[company]), lineStyle: { color: c.accent, width: 2.4 }, itemStyle: { color: c.accent } },
        { name: SEGMENT_LABELS[seg], type: "line", showSymbol: false, data: rebase(data.ts.segments[seg]), lineStyle: { color: c.segment[seg], width: 1.4 }, itemStyle: { color: c.segment[seg] } },
        { name: "XLE", type: "line", showSymbol: false, data: rebase(data.ts.symbols.XLE), lineStyle: { color: c.textMuted, type: "dashed", width: 1.2 }, itemStyle: { color: c.textMuted } },
      ],
    };
  }, [data, company, info, range]);

  const ret = data && company ? rangeReturn(data.ts.symbols[company], rangeIdx(data.ts, range)) : null;
  const cluster = data && company ? data.clustering.k5.kmeans.assignments[company] : null;

  return createPortal(
    <AnimatePresence>
      {data && company && info && fund && (
        <>
          <m.div key="scrim" className="scrim panel-scrim" onClick={() => selectCompany(null)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: reduced ? 0 : tokens.motion.fast }} />
          <m.div
            key="panel"
            className="panel"
            role="dialog"
            aria-modal="true"
            aria-label={`${company} detail`}
            initial={reduced ? { opacity: 0 } : { x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={reduced ? { opacity: 0 } : { x: 40, opacity: 0 }}
            transition={{ duration: reduced ? 0 : tokens.motion.base, ease: tokens.motion.ease as [number, number, number, number] }}
            onKeyDown={trap}
          >
            <div className="handle only-mobile" aria-hidden />
            <nav className="crumbs" aria-label="Breadcrumb">
              <button onClick={() => selectCompany(null)}>Sector</button>
              <span aria-hidden>›</span>
              <button onClick={() => { onlySegment(info.segment); selectCompany(null); }}>{SEGMENT_LABELS[info.segment]}</button>
              <span aria-hidden>›</span>
              <span aria-current="page">{company}</span>
            </nav>
            <div className="panel-head">
              <h2>{company}</h2>
              <div className="panel-actions">
                <button className="btn" aria-pressed={pins.includes(company)} onClick={() => togglePin(company)}>
                  {pins.includes(company) ? "Unpin" : "Pin to compare"}
                </button>
                <button className="btn" onClick={() => selectCompany(null)} aria-label="Close detail" autoFocus>
                  ✕
                </button>
              </div>
            </div>
            <dl className="facts">
              <div><dt>Oil beta</dt><dd className="num">{info.beta.toFixed(2)}</dd><dd className="sub num">CI {info.ci95[0].toFixed(2)}–{info.ci95[1].toFixed(2)}</dd></div>
              <div><dt>Return in range</dt><dd className="num">{pct(ret, 0)}</dd><dd className="sub">{range ? `${range[0]} → ${range[1]}` : "2015 → today"}</dd></div>
              <div><dt>Revenue FY{fund.fiscal_year_end.slice(0, 4)}</dt><dd className="num">{usdBn(fund.revenue)}</dd><dd className="sub">Mkt cap {usdBn(fund.market_cap)}</dd></div>
              <div><dt>Cluster</dt><dd className="num">{cluster != null ? cluster + 1 : "n/a"}</dd><dd className="sub">k-means, k=5</dd></div>
            </dl>
            <h3 className="label">Indexed to 100 at range start</h3>
            {option && <EChart option={option} label={`${company} price index against its segment and XLE`} height={200} />}
            <h3 className="label" style={{ marginTop: 16 }}>Fundamentals vs segment</h3>
            <table className="ratios">
              <thead><tr><th>Ratio</th><th>{company}</th><th>Seg. median</th><th>Pctile</th></tr></thead>
              <tbody>
                {RATIOS.map((r) => (
                  <tr key={r}>
                    <td>{RATIO_LABELS[r]}</td>
                    <td className="num">{pct(fund[r])}</td>
                    <td className="num">{pct(data.fundamentals.segment_median[info.segment][r])}</td>
                    <td className="num">{pct(fund.segment_percentile[r], 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="stamp"><span>Sources: yfinance, SEC EDGAR 10-K (filed by {data.fundamentals.as_of})</span></p>
          </m.div>
        </>
      )}
    </AnimatePresence>,
    document.body,
  );
}
