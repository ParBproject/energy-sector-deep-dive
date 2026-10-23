import { m, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";
import { tokens } from "../design/tokens";

interface Props {
  id: string;
  title: string;
  description?: string;
  source?: string;
  asOf?: string;
  loading?: boolean;
  span?: 4 | 5 | 6 | 7 | 8 | 12;
  /** Replaces the Source / As-of footer with one provenance line (used by EIA charts). */
  stamp?: string;
  children?: ReactNode;
}

export function Skeleton({ label = "Loading chart" }: { label?: string }) {
  return <div className="skeleton" role="status" aria-label={label} />;
}

export function ChartCard({ id, title, description, source, asOf, loading, span = 6, stamp, children }: Props) {
  const reduced = useReducedMotion();
  return (
    <m.article
      id={id}
      className={`card span-${span}`}
      aria-labelledby={`${id}-title`}
      initial={reduced ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: tokens.motion.base, ease: tokens.motion.ease as [number, number, number, number] }}
    >
      <h2 id={`${id}-title`}>{title}</h2>
      {description && <p className="desc">{description}</p>}
      {loading ? <Skeleton /> : children}
      <footer className="stamp">
        {stamp ? (
          <span className="num" data-testid="eia-stamp">{stamp}</span>
        ) : (
          <>
            <span>Source: {source ?? "…"}</span>
            {asOf && <span className="num">As of {asOf}</span>}
          </>
        )}
      </footer>
    </m.article>
  );
}
