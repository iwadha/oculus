"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import DashboardShell from "@/components/layouts/dashboard-shell";
import { PageHeader } from "@/components/layouts/page-header";
import LiveTradesTable from "@/components/trades/LiveTradesTable";
import { api } from "@/lib/api";

type TradesResponse = {
  items: any[];
  page: number;
  page_size: number;
  total: number;
};

const DEFAULT_PAGE_SIZE = 50;

export default function TradesPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const page = Number(searchParams.get("page") || "1");
  const pageSize = DEFAULT_PAGE_SIZE;

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["trades", page, pageSize],
    queryFn: async (): Promise<TradesResponse> => {
      const res = await api.getTrades(page, pageSize);
      return res as TradesResponse;
    },
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages =
    total && pageSize ? Math.max(1, Math.ceil(total / pageSize)) : 1;

  const handlePageChange = (next: number) => {
    const clamped = Math.min(Math.max(next, 1), totalPages || 1);
    const sp = new URLSearchParams(searchParams.toString());
    sp.set("page", String(clamped));
    router.push(`/trades?${sp.toString()}`);
  };

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-4">
        <PageHeader
          title="Live Trades"
          subtitle="All trades detected from Helius and enriched by Oculus."
        />

        {/* Summary / controls */}
        <div className="flex items-center justify-between text-xs">
          <div className="text-muted-foreground">
            {total
              ? `Showing page ${page} of ${totalPages} · ${total.toLocaleString()} trades`
              : "No trades yet. Once ingestion starts, trades will appear here."}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handlePageChange(page - 1)}
              disabled={page <= 1}
              className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium disabled:opacity-40 bg-background hover:bg-accent"
            >
              Prev
            </button>
            <button
              type="button"
              onClick={() => handlePageChange(page + 1)}
              disabled={page >= totalPages}
              className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium disabled:opacity-40 bg-background hover:bg-accent"
            >
              Next
            </button>
            <button
              type="button"
              onClick={() => refetch()}
              className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium bg-background hover:bg-accent"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="border rounded-2xl bg-card">
          {isError && (
            <div className="p-4 text-sm text-red-500">
              Failed to load trades.
            </div>
          )}

          {isLoading && !items.length && !isError && (
            <div className="p-6 text-sm text-muted-foreground">
              Loading trades…
            </div>
          )}

          {!isLoading && !items.length && !isError && (
            <div className="p-6 text-sm text-muted-foreground">
              No trades yet. Once Helius ingestion is running, trades will
              appear here.
            </div>
          )}

          {items.length > 0 && (
            <LiveTradesTable rows={items} pageSize={pageSize} />
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
