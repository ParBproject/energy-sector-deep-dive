import type { Segment } from "../design/tokens";

export interface DataIndex {
  as_of: string;
  snapshot_built_at: string;
  files: string[];
  sources: Record<string, string>;
}
export interface Beta { beta: number; se_hac: number; t_hac: number; ci95: [number, number]; r2: number; n: number }
export interface ReturnsResult {
  as_of: string;
  betas: { companies: Record<string, Beta & { segment: Segment }>; segments: Record<Segment, Beta>; benchmarks: Record<string, Beta> };
  highest_beta_segment: Segment;
  drawdowns: Record<string, Record<string, { max_drawdown: number; peak: string; trough: string }>>;
}
export interface SizingResult { latest_fiscal_year: number; total_revenue_latest_usd: number; companies_reporting_by_year: Record<string, number> }
export interface FactorResult {
  sample: { first_week: string; last_week: string; n_weeks: number };
  walk_forward_explanatory: Record<Segment, { vs_hist_mean: number }>;
  walk_forward_predictive_lag1: Record<Segment, { vs_hist_mean: number }>;
}
export interface ClusteringResult { k5: { kmeans: { adjusted_rand_vs_segments: number; silhouette: number } } }
export interface ScenarioBand { expected_pct: number; param_band_pct: [number, number] }
export interface ScenarioResult {
  weekly_betas: Record<Segment, { beta: number; se_hac: number }>;
  grid: Record<string, Record<Segment, ScenarioBand>>;
  forecaster_input: { implied_move_pct?: number; target_week?: string; model?: string; status: string };
}
export interface AllData {
  index: DataIndex;
  returns: ReturnsResult;
  sizing: SizingResult;
  factor: FactorResult;
  clustering: ClusteringResult;
  scenarios: ScenarioResult;
}
