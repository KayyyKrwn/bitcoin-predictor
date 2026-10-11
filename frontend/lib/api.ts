const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Metrics {
  MSE: number;
  RMSE: number;
  MAE: number;
  MAPE: number;
  R2: number;
  n_test: number;
  test_start: string;
  test_end: string;
}

export interface Point {
  date: string;
  close: number;
}

export interface PredictResponse {
  live_price: number;
  live_date: string;
  pred_price: number;
  pred_date: string;
  delta: number;
  delta_pct: number;
  metrics: Metrics;
  recent: Point[];
}

export interface HistoryResponse {
  start: string;
  end: string;
  count: number;
  first_price: number;
  last_price: number;
  ath: number;
  ath_date: string;
  gain_pct: number;
  points: Point[];
}

export interface Hyperparams {
  ticker: string;
  lookback: number;
  horizon: number;
  n_blocks: number;
  units: number;
  learning_rate: number;
  batch_size: number;
  epochs: number;
}

export interface ComparisonRow {
  model: string;
  optimizer: string;
  rmse: number;
  mae: number;
  mape: number;
  r2: number;
  best: boolean;
}

export interface TestPoint {
  date: string;
  actual: number;
  predicted: number;
}

export interface ModelResponse {
  hyperparams: Hyperparams;
  metrics: Metrics;
  comparison: ComparisonRow[];
  test_predictions: TestPoint[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  predict: () => get<PredictResponse>("/api/predict"),
  history: () => get<HistoryResponse>("/api/history"),
  model: () => get<ModelResponse>("/api/model"),
};

export const API_DOCS_URL = `${API_BASE}/docs`;
