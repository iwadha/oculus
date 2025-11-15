"use client";

import * as React from "react";
import type { WalletOpsRow } from "@/lib/api";
import { fmtNum } from "@/components/tables/column-helpers";
import { ExecutionScoreBadge } from "@/components/ui/ExecutionScoreBadge";
import { api } from "@/lib/api";

type Props = {
  wallet: WalletOpsRow | null;
  open: boolean;
  onClose: () => void;
};

export default function WalletDetailModal({ wallet, open, onClose }: Props) {
  const [trades, setTrades] = React.useState<any[]>([]);
  const [alerts, setAlerts] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (!wallet || !open) return;
    let cancelled = false;

    (async () => {
      setLoading(true);
      try {
        const [t, aRes] = await Promise.all([
          api.getWalletTrades(wallet.id, 20),
          api.getWalletAlerts(wallet.id, 20),
        ]);
        if (cancelled) return;

        setTrades(t ?? []);
        const alertsArr = Array.isArray((aRes as any).items)
          ? (aRes as any).items
          : Array.isArray(aRes)
          ? (aRes as any)
          : [];
        setAlerts(alertsArr);
      } catch {
        if (!cancelled) {
          setTrades([]);
          setAlerts([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [wallet, open]);

  if (!open || !wallet) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border bg-popover shadow-xl">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="space-y-1">
            <div className="text-sm font-semibold">
              {wallet.label || "Wallet"} · {wallet.id}
            </div>
            <div className="text-[11px] text-muted-foreground">
              State: {wallet.state || "UNKNOWN"}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
          >
            Close
          </button>
        </div>

        <div className="px-4 py-3 space-y-4 overflow-y-auto max-h-[calc(90vh-52px)]">
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <Stat label="PnL (SOL)" value={fmtNum(wallet.total_pnl_sol, 3)} />
            <Stat label="ROI %" value={fmtNum(wallet.roi_pct, 1)} />
            <Stat
              label="Trades 7d"
              value={wallet.trades_7d?.toLocaleString() ?? "—"}
            />
            <div className="rounded-2xl border bg-background px-3 py-2">
              <div className="text-[11px] text-muted-foreground">
                Exec score 7d
              </div>
              <div className="mt-1">
                <ExecutionScoreBadge
                  score={
                    typeof wallet.avg_exec_score_7d === "number"
                      ? wallet.avg_exec_score_7d
                      : null
                  }
                />
              </div>
            </div>
          </div>

          {/* Trades / Alerts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <section className="space-y-1">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Recent trades
              </div>
              <div className="rounded-2xl border bg-background p-2 max-h-64 overflow-auto">
                {loading && !trades.length && (
                  <div className="text-xs text-muted-foreground">
                    Loading trades…
                  </div>
                )}
                {!loading && !trades.length && (
                  <div className="text-xs text-muted-foreground">
                    No trades for this wallet yet.
                  </div>
                )}
                {trades.map((t) => (
                  <div
                    key={t.id ?? t.trade_id ?? t.tx_sig}
                    className="flex items-center justify-between py-1 border-b last:border-b-0"
                  >
                    <div className="flex flex-col">
                      <span className="text-[11px]">
                        {(t.side || t.action || "").toUpperCase()}{" "}
                        {t.token_symbol || t.symbol || t.mint || ""}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {t.timestamp &&
                          new Date(t.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-right font-mono text-[11px]">
                      {fmtNum(t.size_sol ?? t.size ?? t.amount, 4)} SOL
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="space-y-1">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                Alerts
              </div>
              <div className="rounded-2xl border bg-background p-2 max-h-64 overflow-auto">
                {loading && !alerts.length && (
                  <div className="text-xs text-muted-foreground">
                    Loading alerts…
                  </div>
                )}
                {!loading && !alerts.length && (
                  <div className="text-xs text-muted-foreground">
                    No alerts for this wallet yet.
                  </div>
                )}
                {alerts.map((a: any) => (
                  <div
                    key={a.id}
                    className="flex flex-col border-b last:border-b-0 py-1"
                  >
                    <span className="text-[11px] font-medium">
                      {a.rule_name || a.type || "Alert"}
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {a.reason || a.message || ""}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border bg-background px-3 py-2">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 text-xs font-semibold">{value}</div>
    </div>
  );
}
