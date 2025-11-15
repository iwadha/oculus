export type Confidence = "HIGH" | "MED" | "LOW" | "NONE";

export type TradeSide = {
  trade_id?: string | number;
  ts?: string | null;
  slot?: number | null;
  price?: number | null;
  roi_pct?: number | null;
  tip_lamports?: number | null;
  cu_used?: number | null;
  cu_price_micro_lamports?: number | null;
  tx_route?: string | null;
};

export type Deltas = {
  slots?: number | null;
  ms?: number | null;
  price_drift_pct?: number | null;
  roi_delta_pct?: number | null;
};

export type Diagnostics = {
  cause?: string | null;
  detail?: string | null;
};

export type ComparePayload = {
  pair_id?: string | null;
  side?: "BUY" | "SELL";
  token_mint?: string;
  copy: TradeSide;
  source: TradeSide;
  deltas: Deltas;
  diagnostics: Diagnostics;
  confidence: Confidence;
};

export type AwaitingPayload = {
  status: "AWAITING_MATCH";
  message: string;
  confidence: Confidence;
};

export type CompareResponse = ComparePayload | AwaitingPayload;
