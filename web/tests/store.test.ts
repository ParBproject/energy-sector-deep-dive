import { beforeEach, describe, expect, it } from "vitest";
import { SEGMENTS } from "../src/design/tokens";
import { startUrlSync, urlStateOf, useStore } from "../src/state/store";
import { DEFAULT_URL_STATE, MAX_PINS, parse, serialize, type UrlState } from "../src/state/url";

const reset = () => useStore.setState({ ...DEFAULT_URL_STATE, segments: [...SEGMENTS], pins: [], sheetOpen: false });

describe("url serialize/parse", () => {
  it("omits defaults", () => expect(serialize(DEFAULT_URL_STATE)).toBe("#/overview"));
  it("round-trips a full state", () => {
    const s: UrlState = { view: "returns", segments: ["upstream", "refiners"], company: "XOM", pins: ["CVX", "EOG"], range: ["2020-01-03", "2022-12-30"], oil: 15, oilSource: "forecaster" };
    const h = serialize(s);
    expect(h).toBe("#/returns?seg=upstream,refiners&co=XOM&pin=CVX,EOG&range=2020-01-03_2022-12-30&oil=15&src=forecaster");
    expect(parse(h)).toEqual(s);
  });
  it("rejects junk and falls back to defaults", () => {
    const p = parse("#/nope?seg=foo,majors&co=<script>&pin=AAA,AAA,BBB,CCC,DDD,EEE&range=2022-01-01_2020-01-01&oil=abc&src=evil");
    expect(p.view).toBe("overview");
    expect(p.segments).toEqual(["majors"]);
    expect(p.company).toBeNull();
    expect(p.pins).toEqual(["AAA", "BBB", "CCC", "DDD"]);
    expect(p.range).toBeNull();
    expect(p.oil).toBe(DEFAULT_URL_STATE.oil);
    expect(p.oilSource).toBe("slider");
  });
  it("clamps the oil move", () => expect(parse("#/scenario?oil=900").oil).toBe(50));
  it("keeps segment order canonical", () => expect(parse("#/?seg=services,majors").segments).toEqual(["majors", "services"]));
  it("handles empty hash", () => expect(parse("")).toEqual(DEFAULT_URL_STATE));
});

describe("store actions", () => {
  beforeEach(reset);
  it("never deselects the last segment", () => {
    const st = useStore.getState();
    st.onlySegment("upstream");
    useStore.getState().toggleSegment("upstream");
    expect(useStore.getState().segments).toEqual(["upstream"]);
  });
  it("toggles segments in canonical order", () => {
    useStore.getState().onlySegment("services");
    useStore.getState().toggleSegment("majors");
    expect(useStore.getState().segments).toEqual(["majors", "services"]);
  });
  it("pins at most four companies, dropping the oldest", () => {
    for (const t of ["A", "B", "C", "D", "E"]) useStore.getState().togglePin(t);
    expect(useStore.getState().pins).toEqual(["B", "C", "D", "E"]);
    expect(useStore.getState().pins).toHaveLength(MAX_PINS);
    useStore.getState().togglePin("C");
    expect(useStore.getState().pins).toEqual(["B", "D", "E"]);
  });
  it("moving the slider switches the source back to slider", () => {
    useStore.getState().setOilSource("forecaster");
    useStore.getState().setOil(5);
    expect(useStore.getState()).toMatchObject({ oil: 5, oilSource: "slider" });
  });
});

function fakeWindow(hash: string) {
  const listeners: Record<string, Array<() => void>> = {};
  const win = {
    location: { hash },
    history: {
      calls: [] as string[],
      replaceState(_: unknown, __: string, url: string) {
        win.history.calls.push(url);
        win.location.hash = url;
      },
    },
    addEventListener: (t: string, f: () => void) => ((listeners[t] ??= []).push(f)),
    removeEventListener: (t: string, f: () => void) => (listeners[t] = (listeners[t] ?? []).filter((g) => g !== f)),
    fire: (t: string) => (listeners[t] ?? []).forEach((f) => f()),
    count: (t: string) => (listeners[t] ?? []).length,
  };
  return win;
}

describe("URL sync", () => {
  beforeEach(reset);
  it("hydrates the store from the initial URL", () => {
    const w = fakeWindow("#/clusters?co=OXY&seg=upstream");
    const stop = startUrlSync(w as never);
    expect(useStore.getState()).toMatchObject({ view: "clusters", company: "OXY", segments: ["upstream"] });
    stop();
  });
  it("writes store changes to the URL with replaceState", () => {
    const w = fakeWindow("#/overview");
    const stop = startUrlSync(w as never);
    useStore.getState().selectCompany("XOM");
    useStore.getState().setRange(["2020-01-03", "2020-12-25"]);
    expect(w.location.hash).toBe("#/overview?co=XOM&range=2020-01-03_2020-12-25");
    expect(parse(w.location.hash)).toEqual(urlStateOf(useStore.getState()));
    stop();
  });
  it("does not write when non-URL state changes", () => {
    const w = fakeWindow("#/overview");
    const stop = startUrlSync(w as never);
    useStore.getState().setSheet(true);
    expect(w.history.calls).toHaveLength(0);
    stop();
  });
  it("follows back/forward (hashchange) into the store", () => {
    const w = fakeWindow("#/overview");
    const stop = startUrlSync(w as never);
    w.location.hash = "#/scenario?oil=20";
    w.fire("hashchange");
    expect(useStore.getState()).toMatchObject({ view: "scenario", oil: 20 });
    expect(w.history.calls).toHaveLength(0); // no write-back loop
    stop();
    expect(w.count("hashchange")).toBe(0);
  });
});
