import type { Segment } from "../design/tokens";

export interface DataIndex { as_of: string; snapshot_built_at: string; files: string[]; sources: Record<string, string> }
export interface Beta { beta: number; se_hac: number; t_hac: number; ci95: [number, number]; r2: number; n: number }
export interface Drawdown { max_drawdown: number; peak: string; trough: string }
export interface ReturnsResult {
  as_of: string;
  betas: { companies: Record<string, Beta & { segment: Segment }>; segments: Record<Segment, Beta>; benchmarks: Record<string, Beta> };
  highest_beta_segment: Segment;
  lowest_beta_segment: Segment;
  correlations: { window_days: number; latest: Record<string, { wti: number; spx: number }> };
  drawdowns: Record<string, Record<string, Drawdown>>;
}
export interface SizingResult {
  latest_fiscal_year: number;
  total_revenue_latest_usd: number;
  segment_revenue_usd: Record<Segment, Record<string, number | null>>;
  segment_share_latest: Record<Segment, number>;
  missing_revenue_latest_year: string[];
  caveats: string[];
}
export const RATIOS = ["capex_intensity", "reinvestment_rate", "fcf_yield", "debt_to_capital", "payout_ratio"] as const;
export type Ratio = (typeof RATIOS)[number];
export interface CompanyFundamentals extends Record<Ratio, number | null> {
  segment: Segment;
  fiscal_year_end: string;
  revenue: number | null;
  cfo: number | null;
  capex: number | null;
  fcf: number | null;
  market_cap: number | null;
  price: number;
  segment_percentile: Record<Ratio, number | null>;
}
export interface FundamentalsResult {
  as_of: string;
  definitions: Record<Ratio, string>;
  segment_median: Record<Segment, Record<Ratio, number | null>>;
  companies: Record<string, CompanyFundamentals>;
}
export interface FactorResult {
  sample: { first_week: string; last_week: string; n_weeks: number };
  factors: string[];
  crack_spread_proxy: string;
  dollar_proxy: string;
  full_sample: Record<Segment, { coef: Record<string, number>; t_hac: Record<string, number>; r2: number }>;
  walk_forward_explanatory: Record<Segment, { vs_hist_mean: number; vs_zero: number }>;
  walk_forward_predictive_lag1: Record<Segment, { vs_hist_mean: number; vs_zero: number }>;
}
export interface ClusteringResult {
  features: string[];
  silhouette_by_k: Record<"kmeans" | "ward", Record<string, number>>;
  k5: Record<"kmeans" | "ward", { adjusted_rand_vs_segments: number; silhouette: number; assignments: Record<string, number> }>;
  silhouette_of_true_segments: number;
  imputed_cells: Record<string, string[]>;
  n_imputed_cells: number;
  pca: { explained_variance_ratio: [number, number]; coords: Record<string, [number, number]>; segment: Record<string, Segment> };
}
export interface ScenarioBand { expected_pct: number; param_band_pct: [number, number]; prediction_band_pct: [number, number] }
export interface ForecasterInput {
  status: string;
  model?: string;
  origin_week?: string;
  target_week?: string;
  implied_move_pct?: number;
  realized_move_pct?: number;
  source_commit?: string;
  vendored_on?: string;
}
export interface ScenarioResult {
  framing: string;
  weekly_betas: Record<Segment, { beta: number; se_hac: number; resid_sd: number; r2: number }>;
  grid: Record<string, Record<Segment, ScenarioBand>>;
  forecaster_input: ForecasterInput;
}
export interface TimeSeries { dates: string[]; segments: Record<Segment, number[]>; symbols: Record<string, (number | null)[]> }
export interface AllData {
  index: DataIndex;
  returns: ReturnsResult;
  sizing: SizingResult;
  fundamentals: FundamentalsResult;
  factor: FactorResult;
  clustering: ClusteringResult;
  scenarios: ScenarioResult;
  ts: TimeSeries;
}
