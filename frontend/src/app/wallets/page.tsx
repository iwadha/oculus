"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import DashboardShell from "@/components/layouts/dashboard-shell"; // adjust path
import { PageHeader } from "@/components/layouts/page-header";
import { api, type WalletOpsRow } from "@/lib/api";
import { WalletOpsGrid } from "@/components/wallets/WalletOpsGrid";
import { WalletDetailModal } from "@/components/wallets/WalletDetailModal";

export default function WalletsPage() {
  const [selectedWallet, setSelectedWallet] = React.useState<WalletOpsRow | null>(null);

  const { data, isLoading, isError, refetch } = useQuery<WalletOpsRow[]>({
    queryKey: ["wallet-ops"],
    queryFn: () => api.getWalletOps(),
    refetchInterval: 30000,
  });

  const rows = data ?? [];

  // simple aggregates (you can make these smarter later)
  const activeCount = rows.filter((w) => w.state === "ACTIVE").length;
  const totalPnl = rows.reduce((acc, w) => acc + (w.total_pnl_sol ?? 0), 0);
  const avgExec =
    rows.length > 0
      ? rows.reduce((acc, w) => acc + (w.avg_exec_score_7d ?? 0), 0) / rows.length
      : 0;

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-4">
        <PageHeader
          title="Wallet Operations"
          subtitle="Fleet view of all copy wallets with performance, risk, and state control."
        />

        {/* Metrics row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <MetricCard
            label="Total wallets"
            value={rows.length}
            hint="Tracked in Wallet Ops"
          />
          <MetricCard
            label="Active wallets"
            value={activeCount}
            hint="State = ACTIVE"
          />
          <MetricCard
            label="Fleet PnL (SOL)"
            value={totalPnl}
            format="number"
          />
          <MetricCard
            label="Avg exec score (7d)"
            value={avgExec}
            format="fixed1"
          />
        </div>

        {/* Table */}
        <div className="border rounded-2xl bg-card">
          <div className="flex items-center justify-between px-4 py-2 text-xs">
            <div className="text-muted-foreground">
              {rows.length
                ? `Managing ${rows.length.toLocaleString()} wallets`
                : "No wallets found yet"}
            </div>
            <button
              type="button"
              onClick={() => refetch()}
              className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium bg-background hover:bg-accent"
            >
              Refresh
            </button>
          </div>

          {isError && (
            <div className="p-4 text-sm text-red-500">
              Failed to load wallet ops.
            </div>
          )}

          {isLoading && !rows.length && !isError && (
            <div className="p-6 text-sm text-muted-foreground">
              Loading wallet data…
            </div>
          )}

          {!isLoading && !rows.length && !isError && (
            <div className="p-6 text-sm text-muted-foreground">
              No wallet ops data yet. Once copy wallets are configured and trades
              are ingested, wallets will appear here.
            </div>
          )}

          {rows.length > 0 && (
            <WalletOpsGrid
              rows={rows}
              onRowClick={(row) => setSelectedWallet(row)}
            />
          )}
        </div>

        {selectedWallet && (
          <WalletDetailModal
            wallet={selectedWallet}
            open={!!selectedWallet}
            onClose={() => setSelectedWallet(null)}
          />
        )}
      </div>
    </DashboardShell>
  );
}

type MetricCardProps = {
  label: string;
  value: number;
  hint?: string;
  format?: "number" | "fixed1";
};

function MetricCard({ label, value, hint, format }: MetricCardProps) {
  const display =
    format === "fixed1"
      ? Number.isFinite(value)
        ? value.toFixed(1)
        : "—"
      : Number.isFinite(value)
      ? value.toLocaleString()
      : "—";

  return (
    <div className="rounded-2xl border bg-card px-3 py-2 flex flex-col justify-between">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">{display}</div>
      {hint && (
        <div className="mt-0.5 text-[11px] text-muted-foreground">{hint}</div>
      )}
    </div>
  );
}
