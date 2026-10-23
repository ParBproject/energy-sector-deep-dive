import { AnimatePresence, m, useReducedMotion } from "framer-motion";
import { createPortal } from "react-dom";
import { SEGMENTS, tokens } from "../design/tokens";
import { SEGMENT_LABELS } from "../format";
import { useStore } from "../state/store";

function Chips() {
  const { segments, toggleSegment } = useStore();
  return (
    <>
      {SEGMENTS.map((s) => (
        <button key={s} className="chip" aria-pressed={segments.includes(s)} onClick={() => toggleSegment(s)}>
          <span className="dot" style={{ background: tokens.color.segment[s] }} aria-hidden />
          {SEGMENT_LABELS[s]}
        </button>
      ))}
    </>
  );
}

/** Keyboard/screen-reader path to the company drill-down (charts are canvas). */
function CompanyPicker({ className }: { className?: string }) {
  const { data, company, selectCompany, segments } = useStore();
  const tickers = Object.entries(data?.returns.betas.companies ?? {}).filter(([, v]) => segments.includes(v.segment)).map(([t]) => t).sort();
  return (
    <label className={`picker ${className ?? ""}`}>
      <span className="sr-only">Open company detail</span>
      <select value={company ?? ""} onChange={(e) => selectCompany(e.target.value || null)}>
        <option value="">Company…</option>
        {tickers.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
    </label>
  );
}

function Context() {
  const { pins, togglePin, selectCompany, range, setRange } = useStore();
  return (
    <>
      {range && (
        <button className="chip ctx" aria-pressed="true" onClick={() => setRange(null)} aria-label="Clear date range">
          <span className="num">{range[0]} → {range[1]}</span> ✕
        </button>
      )}
      {pins.map((p) => (
        <span key={p} className="pin">
          <button className="chip ctx" aria-pressed="true" onClick={() => selectCompany(p)}>📌 {p}</button>
          <button className="chip x" onClick={() => togglePin(p)} aria-label={`Unpin ${p}`}>✕</button>
        </span>
      ))}
    </>
  );
}

export function FilterBar({ asOf }: { asOf?: string }) {
  const { segments, sheetOpen, setSheet, resetSegments, pins, range } = useStore();
  const reduced = useReducedMotion();
  const extra = pins.length + (range ? 1 : 0);
  return (
    <div className="filterbar" role="region" aria-label="Filters">
      <div className="container row">
        <span className="label only-desktop">Segments</span>
        <span className="desktop-chips">
          <Chips />
          <Context />
        </span>
        <CompanyPicker className="only-desktop" />
        <button className="btn only-mobile" onClick={() => setSheet(true)} aria-haspopup="dialog">
          Filters <span className="badge num">{segments.length}/5{extra ? ` +${extra}` : ""}</span>
        </button>
        <span className="label num asof">{asOf ? `As of ${asOf}` : "Loading…"}</span>
      </div>
      {createPortal(
        <AnimatePresence>
          {sheetOpen && (
            <>
              <m.div key="scrim" className="scrim" onClick={() => setSheet(false)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
              <m.div
                key="sheet"
                className="sheet"
                role="dialog"
                aria-modal="true"
                aria-label="Filters"
                initial={reduced ? { opacity: 0 } : { y: "100%" }}
                animate={reduced ? { opacity: 1 } : { y: 0 }}
                exit={reduced ? { opacity: 0 } : { y: "100%" }}
                transition={{ duration: reduced ? 0 : tokens.motion.base, ease: tokens.motion.ease as [number, number, number, number] }}
                drag={reduced ? false : "y"}
                dragConstraints={{ top: 0, bottom: 0 }}
                dragElastic={{ top: 0, bottom: 0.6 }}
                onDragEnd={(_, info) => info.offset.y > 80 && setSheet(false)}
              >
                <div className="handle" aria-hidden />
                <div className="label">Segments</div>
                <div className="chips"><Chips /></div>
                <div className="label">Company detail</div>
                <CompanyPicker />
                {extra > 0 && (<><div className="label">Range &amp; pinned</div><div className="chips"><Context /></div></>)}
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn" onClick={resetSegments}>Reset</button>
                  <button className="btn primary" style={{ flex: 1 }} onClick={() => setSheet(false)}>Show results</button>
                </div>
              </m.div>
            </>
          )}
        </AnimatePresence>,
        document.body,
      )}
    </div>
  );
}
