"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import LiveTradesTable from "@/components/trades/LiveTradesTable"; // path to your upgraded table

export function RecentTradesCard() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["recent-trades"],
    queryFn: () => api.getRecentTrades(20),
    refetchInterval: 10000,
  });

  const rows = data ?? [];

  return (
    <div className="rounded-2xl border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            Latest Trades
          </div>
          <div className="text-sm text-muted-foreground">
            Last 20 ingested trades
          </div>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium bg-background hover:bg-accent"
        >
          Refresh
        </button>
      </div>

      {isLoading && (
        <div className="py-6 text-sm text-muted-foreground">Loading…</div>
      )}

      {isError && !isLoading && (
        <div className="py-6 text-sm text-red-500">
          Failed to load recent trades.
        </div>
      )}

      {!isLoading && !rows.length && !isError && (
        <div className="py-6 text-sm text-muted-foreground">
          No trades yet. Once ingestion is running, trades will appear here.
        </div>
      )}

      {rows.length > 0 && (
        <div className="-mx-2 -my-1">
          {/* For dashboard we can show read-only, no pagination */}
          <LiveTradesTable
            data={rows}
            page={1}
            pageSize={rows.length}
            total={rows.length}
          />
        </div>
      )}
    </div>
  );
}
