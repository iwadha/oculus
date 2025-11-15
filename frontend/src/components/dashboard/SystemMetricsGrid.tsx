"use client";

import * as React from "react";
import type { SystemMetrics } from "@/lib/api";

export function SystemMetricsGrid({ metrics }: { metrics: SystemMetrics | undefined }) {
  if (!metrics) {
    return (
      <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
        Loading system metrics…
      </div>
    );
  }

  const items = [
    {
      label: "Trades today",
      value: metrics.trades_today,
      hint: "Last 24h",
    },
    {
      label: "Active wallets",
      value: metrics.unique_wallets,
      hint: "Trading in the last 24h",
    },
    {
      label: "Active creators",
      value: metrics.active_creators,
      hint: "Creators with trades in last 7d",
    },
    {
      label: "Pending alerts",
      value: metrics.pending_alerts,
      hint: "Unresolved",
    },
    {
      label: "Unscored pairs",
      value: metrics.unscored_pairs,
      hint: "Need scoring",
    },
    {
      label: "Tokens tracked",
      value: metrics.token_count,
      hint: "With metadata",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {items.map((it) => (
        <div
          key={it.label}
          className="rounded-2xl border bg-card px-3 py-2 flex flex-col justify-between"
        >
          <div className="text-[11px] text-muted-foreground">{it.label}</div>
          <div className="mt-1 text-lg font-semibold">
            {typeof it.value === "number" ? it.value.toLocaleString() : "—"}
          </div>
          {it.hint && (
            <div className="mt-0.5 text-[11px] text-muted-foreground">
              {it.hint}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
