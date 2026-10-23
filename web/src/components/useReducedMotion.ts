import { useEffect, useState } from "react";

const Q = "(prefers-reduced-motion: reduce)";

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => typeof window !== "undefined" && window.matchMedia(Q).matches);
  useEffect(() => {
    const mq = window.matchMedia(Q);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}
