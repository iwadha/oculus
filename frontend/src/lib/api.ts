import { fetchJson } from "@/lib/http";
import { API_BASE } from "@/lib/constants";
import type {
  KpiResponse,
  CompareResponse,
  LadderResponse,
  Alert,
} from "@/lib/types";

// ================== System / Diagnostics ==================

export type SystemStatus = {
  status: "ok" | "degraded" | string;
  env: string;
  version: string;
  stream_source: string;
  database: string;
  workers: Record<string, boolean>;
  last_updates: Record<string, string>;
  timestamp: string;
};

export type SystemMetrics = {
  timestamp: string;
  trades_today: number;
  unique_wallets: number;
  unscored_pairs: number;
  active_creators: number;
  pending_alerts: number;
  token_count: number;
  last_trade_ts: string | null;
};

// ================== Wallet Ops ==================

export type WalletOpsRow = {
  id: string;
  label?: string | null;
  state?: "ACTIVE" | "BUY_ONLY" | "SELL_ONLY" | "PAUSED" | "REMOVED" | string;
  total_pnl_sol?: number | null;
  total_invested_sol?: number | null;
  roi_pct?: number | null;
  trades_24h?: number | null;
  trades_7d?: number | null;
  alerts_open?: number | null;
  avg_exec_score_7d?: number | null;
  last_trade_ts?: string | null;
};

// ================== Alerts & Rules ==================

export type RuleRow = {
  id: string;
  name: string;
  description?: string | null;
  severity?: string | null;
  enabled?: boolean;
  scope?: string | null; // e.g. "wallet", "creator", "fleet"
  created_at?: string | null;
};

export const api = {
  // ---------- Dashboard / KPIs ----------
  getKpis: (): Promise<KpiResponse> =>
    fetchJson<KpiResponse>(`${API_BASE}/v1/kpis`),

  // ---------- Trades & Analysis ----------
  getTrades: (page = 1, pageSize = 50): Promise<any> =>
    fetchJson<any>(
      `${API_BASE}/v1/trades?page=${page}&page_size=${pageSize}`
    ),

  getCompare: (tradeId: string): Promise<CompareResponse> =>
    fetchJson<CompareResponse>(
      `${API_BASE}/v1/trades/${tradeId}/compare`
    ),

  getLadder: (tradeId: string | number, win = 8): Promise<LadderResponse> =>
    fetchJson<LadderResponse>(
      `${API_BASE}/v1/trades/${tradeId}/ladder?window_slots=${win}`
    ),

  // ---------- Creators ----------
  getCreatorsCatalog: (qs: URLSearchParams): Promise<any[]> =>
    fetchJson<any[]>(
      `${API_BASE}/v1/creators/catalog?${qs.toString()}`
    ),

  getCreatorProfile: (k: string): Promise<any> =>
    fetchJson<any>(`${API_BASE}/v1/creators/${k}/profile`),

  getCreatorActivity: (k: string, qs: URLSearchParams): Promise<any[]> =>
    fetchJson<any[]>(
      `${API_BASE}/v1/creators/${k}/activity?${qs.toString()}`
    ),

  // ---------- Wallet Ops ----------
  // typed to WalletOpsRow now
  getWalletOps: (): Promise<WalletOpsRow[]> =>
    fetchJson<WalletOpsRow[]>(`${API_BASE}/v1/wallets/ops`),

  setWalletState: (
    id: string,
    state: string,
    reason = "Manual"
  ): Promise<any> =>
    fetchJson<any>(`${API_BASE}/v1/wallets/${id}/state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state, reason }),
    }),

  // Small helper calls used by the Wallet detail modal
  getWalletTrades: (
    walletId: string,
    limit = 20
  ): Promise<any[]> => {
    const qs = new URLSearchParams({
      page: "1",
      page_size: String(limit),
      // adjust param name here to whatever the backend expects
      wallet_id: walletId,
    });
    return fetchJson<any[]>(
      `${API_BASE}/v1/trades?${qs.toString()}`
    );
  },

  getWalletAlerts: (
    walletId: string,
    limit = 20
  ): Promise<{ items: Alert[]; page: number; page_size: number; total: number }> => {
    const qs = new URLSearchParams({
      wallet_id: walletId,
      page: "1",
      page_size: String(limit),
    });
    return fetchJson(
      `${API_BASE}/v1/alerts?${qs.toString()}`
    );
  },

  // ---------- Alerts (paginated) ----------
  // KEEPING your original implementation
  getAlerts: (
    arg?: URLSearchParams | Record<string, any>
  ): Promise<{ items: Alert[]; page: number; page_size: number; total: number }> => {
    const params =
      arg instanceof URLSearchParams
        ? arg
        : new URLSearchParams(Object.entries(arg ?? {}));

    return fetchJson(
      `${API_BASE}/v1/alerts?${params.toString()}`
    );
  },

  // ---------- Rules ----------
  // typed version, but same behavior as your original any[]
  getRules: (): Promise<RuleRow[]> =>
    fetchJson<RuleRow[]>(`${API_BASE}/v1/rules`),

  // ---------- System diagnostics ----------
  getSystemStatus: (): Promise<SystemStatus> =>
    fetchJson<SystemStatus>(`${API_BASE}/v1/system/status`),

  getSystemMetrics: (): Promise<SystemMetrics> =>
    fetchJson<SystemMetrics>(`${API_BASE}/v1/system/metrics`),

  // ---------- Convenience helpers ----------
  getRecentTrades: (limit = 20): Promise<any[]> =>
    fetchJson<any[]>(
      `${API_BASE}/v1/trades?page=1&page_size=${limit}`
    ),
};
