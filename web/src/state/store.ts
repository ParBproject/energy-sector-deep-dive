import { create } from "zustand";
import { SEGMENTS, type Segment } from "../design/tokens";
import type { AllData } from "../data/types";

interface State {
  data: AllData | null;
  error: string | null;
  segments: Segment[];
  oilMove: number;
  sheetOpen: boolean;
  tab: number;
  setData: (d: AllData) => void;
  setError: (e: string) => void;
  toggleSegment: (s: Segment) => void;
  resetSegments: () => void;
  setOilMove: (v: number) => void;
  setSheet: (open: boolean) => void;
  setTab: (i: number) => void;
}

export const useStore = create<State>((set) => ({
  data: null,
  error: null,
  segments: [...SEGMENTS],
  oilMove: -10,
  sheetOpen: false,
  tab: 0,
  setData: (data) => set({ data }),
  setError: (error) => set({ error }),
  toggleSegment: (s) =>
    set((st) => {
      const on = st.segments.includes(s);
      if (on && st.segments.length === 1) return st; // keep at least one
      return { segments: on ? st.segments.filter((x) => x !== s) : SEGMENTS.filter((x) => x === s || st.segments.includes(x)) };
    }),
  resetSegments: () => set({ segments: [...SEGMENTS] }),
  setOilMove: (oilMove) => set({ oilMove }),
  setSheet: (sheetOpen) => set({ sheetOpen }),
  setTab: (tab) => set({ tab }),
}));
