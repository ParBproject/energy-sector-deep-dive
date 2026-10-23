import type { AllData } from "./types";

const base = `${import.meta.env.BASE_URL}data/`;

async function get<T>(name: string): Promise<T> {
  const r = await fetch(base + name);
  if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

export async function loadAll(): Promise<AllData> {
  const [index, returns, sizing, fundamentals, factor, clustering, scenarios, ts] = await Promise.all([
    get<AllData["index"]>("index.json"),
    get<AllData["returns"]>("returns.json"),
    get<AllData["sizing"]>("market_sizing.json"),
    get<AllData["fundamentals"]>("fundamentals.json"),
    get<AllData["factor"]>("factor_model.json"),
    get<AllData["clustering"]>("clustering.json"),
    get<AllData["scenarios"]>("scenarios.json"),
    get<AllData["ts"]>("timeseries.json"),
  ]);
  return { index, returns, sizing, fundamentals, factor, clustering, scenarios, ts };
}
