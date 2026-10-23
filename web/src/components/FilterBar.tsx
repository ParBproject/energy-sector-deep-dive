import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
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
        <button className="btn only-mobile" onClick={() => setSheet(true)} aria-haspopup="dialog">
          Filters <span className="badge num">{segments.length}/5{extra ? ` +${extra}` : ""}</span>
        </button>
        <span className="label num asof">{asOf ? `As of ${asOf}` : "Loading…"}</span>
      </div>
      {createPortal(
        <AnimatePresence>
          {sheetOpen && (
            <>
              <motion.div key="scrim" className="scrim" onClick={() => setSheet(false)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
              <motion.div
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
                {extra > 0 && (<><div className="label">Range &amp; pinned</div><div className="chips"><Context /></div></>)}
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn" onClick={resetSegments}>Reset</button>
                  <button className="btn primary" style={{ flex: 1 }} onClick={() => setSheet(false)}>Show results</button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>,
        document.body,
      )}
    </div>
  );
}
