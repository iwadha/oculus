export type TradeEvent = {
type: "trade";
wallet: string;
action: "BUY" | "SELL";
token: string;
creator?: string | null;
ts: string; // ISO
execution_score?: number | null; // 0..100
source_slot?: number | null;
copy_slot?: number | null;
};


export type KpiResponse = {
active_creators: number;
buy_pct: number; // 0..100
avg_blocks: number; // copy - source
avg_score: number; // 0..100
tps: number; // trades/sec
window: number;
};


export type CompareResponse =
| { status: "AWAITING_MATCH"; message: string; confidence: "LOW" | "MED" | "HIGH" | "NONE" }
| {
token_mint: string;
side: "BUY" | "SELL";
confidence: "HIGH" | "MED" | "LOW" | "NONE";
copy: { trade_id: string; ts: string; price: number; roi_pct: number; tip_lamports: number; cu_used: number; cu_price_micro_lamports: number; tx_route: string };
source: { trade_id: string; ts: string; price: number; roi_pct: number; tip_lamports: number; cu_used: number; cu_price_micro_lamports: number; tx_route: string };
deltas: { slots: number; ms?: number | null; price_drift_pct?: number | null; roi_delta_pct?: number | null };
diagnostics?: { cause?: string; detail?: string };
};


export type LadderResponse = {
pair_id: number;
token_mint?: string | null;
side?: "BUY" | "SELL" | null;
window: number;
event_slot?: number | null;
landed_slot?: number | null;
delta_slots?: number | null;
badges: string[];
efficiency: { tip_grade?: string | null; cu_price_grade?: string | null; notes: string[] };
crowding: { ahead: number; at_event: number; behind: number; total: number; copies_per_slot: { slot: number; relative: number; copies: number; sources: number; tip_avg?: number | null; cu_price_avg?: number | null }[] };
neighbor_fee_stats: { n: number; tip_lamports: { p50?: number | null; p66?: number | null; p90?: number | null }; cu_price_micro_lamports: { p50?: number | null; p66?: number | null; p90?: number | null } };
neighbor_distributions: { tip_lamports_hist: { bin_min?: number | null; bin_max?: number | null; count: number }[]; cu_price_micro_lamports_hist: { bin_min?: number | null; bin_max?: number | null; count: number }[] };
neighbor_samples: { top_ahead: any[]; top_behind: any[] };
copy_tx?: any; source_tx?: any;
};


export type Alert = {
id: string; severity: "INFO" | "WARN" | "CRITICAL"; category: string; reason: string;
wallet_id?: string | null; creator_pubkey?: string | null; resolved: boolean; created_at: string;
eval_snapshot?: Record<string, any>;
};