import { create } from "zustand";
import { SEGMENTS, type Segment } from "../design/tokens";
import type { AllData } from "../data/types";
import { DEFAULT_URL_STATE, MAX_PINS, parse, serialize, type OilSource, type UrlState, type View } from "./url";

export interface State extends UrlState {
  data: AllData | null;
  error: string | null;
  sheetOpen: boolean;
  setData: (d: AllData) => void;
  setError: (e: string) => void;
  setView: (v: View) => void;
  toggleSegment: (s: Segment) => void;
  onlySegment: (s: Segment) => void;
  resetSegments: () => void;
  selectCompany: (t: string | null) => void;
  togglePin: (t: string) => void;
  setRange: (r: [string, string] | null) => void;
  setOil: (v: number) => void;
  setOilSource: (s: OilSource) => void;
  setSheet: (open: boolean) => void;
  hydrate: (u: UrlState) => void;
}

export const useStore = create<State>((set) => ({
  ...DEFAULT_URL_STATE,
  data: null,
  error: null,
  sheetOpen: false,
  setData: (data) => set({ data }),
  setError: (error) => set({ error }),
  setView: (view) => set({ view }),
  toggleSegment: (s) =>
    set((st) => {
      const on = st.segments.includes(s);
      if (on && st.segments.length === 1) return {};
      return { segments: on ? st.segments.filter((x) => x !== s) : SEGMENTS.filter((x) => x === s || st.segments.includes(x)) };
    }),
  onlySegment: (s) => set({ segments: [s] }),
  resetSegments: () => set({ segments: [...SEGMENTS] }),
  selectCompany: (company) => set({ company }),
  togglePin: (t) =>
    set((st) =>
      st.pins.includes(t)
        ? { pins: st.pins.filter((p) => p !== t) }
        : { pins: [...st.pins, t].slice(-MAX_PINS) },
    ),
  setRange: (range) => set({ range }),
  setOil: (oil) => set({ oil, oilSource: "slider" }),
  setOilSource: (oilSource) => set({ oilSource }),
  setSheet: (sheetOpen) => set({ sheetOpen }),
  hydrate: (u) => set(u),
}));

export function urlStateOf(s: UrlState): UrlState {
  const { view, segments, company, pins, range, oil, oilSource } = s;
  return { view, segments, company, pins, range, oil, oilSource };
}

/** Two-way sync between the store and location.hash. Returns an unsubscribe function. */
export function startUrlSync(win: Pick<Window, "location" | "history" | "addEventListener" | "removeEventListener"> = window) {
  useStore.getState().hydrate(parse(win.location.hash));
  let last = serialize(urlStateOf(useStore.getState()));
  const unsub = useStore.subscribe((st) => {
    const next = serialize(urlStateOf(st));
    if (next !== last) {
      last = next;
      win.history.replaceState(null, "", next);
    }
  });
  const onHash = () => {
    const hash = win.location.hash || "#/";
    if (hash === last) return;
    last = hash;
    useStore.getState().hydrate(parse(hash));
  };
  win.addEventListener("hashchange", onHash);
  return () => {
    unsub();
    win.removeEventListener("hashchange", onHash);
  };
}
