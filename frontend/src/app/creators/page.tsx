"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";

import DashboardShell from "@/components/layouts/dashboard-shell";
import { PageHeader } from "@/components/layouts/page-header";
import { DataGrid } from "@/components/tables/data-grid";
import { CreatorBadges } from "@/components/creators/CreatorBadges";
import { ExecutionScoreBadge } from "@/components/ui/ExecutionScoreBadge";
import { fmtInt, fmtNum, fmtDateTime } from "@/components/tables/column-helpers";
import { api } from "@/lib/api";

type CatalogItem = {
  creator_pubkey: string;
  alias?: string | null;
  copyability_tier?: string | null;
  risk_score?: number | null;
  creator_rank?: number | null;
  trades_24h?: number | null;
  trades_7d?: number | null;
  trades_30d?: number | null;
  avg_execution_score_7d?: number | null;
  avg_execution_score_30d?: number | null;
  roi_me_7d?: number | null;
  roi_me_30d?: number | null;
  last_activity?: string | null;
};

export default function CreatorsPage() {
  const router = useRouter();

  const { data, isLoading, isError, refetch } = useQuery<CatalogItem[]>({
    queryKey: ["creators-catalog"],
    queryFn: async () => {
      const qs = new URLSearchParams({
        sort: "rank",
        limit: "200",
      });
      // api.getCreatorsCatalog expects a URLSearchParams
      return api.getCreatorsCatalog(qs);
    },
    refetchInterval: 30000,
  });

  const rows = data ?? [];

  const columns = React.useMemo<ColumnDef<CatalogItem, any>[]>(
    () => [
      {
        id: "rank",
        header: "#",
        accessorKey: "creator_rank",
        cell: (ctx) => (
          <span className="text-xs font-mono text-muted-foreground">
            {ctx.getValue() ?? "—"}
          </span>
        ),
        size: 40,
      },
      {
        id: "alias",
        header: "Creator",
        accessorKey: "alias",
        cell: (ctx) => {
          const row = ctx.row.original;
          return (
            <button
              type="button"
              onClick={() => router.push(`/creators/${row.creator_pubkey}`)}
              className="text-left"
            >
              <div className="flex flex-col">
                <span className="text-sm font-semibold">
                  {row.alias || "Unnamed"}
                </span>
                <span className="text-[11px] font-mono text-muted-foreground">
                  {shortKey(row.creator_pubkey)}
                </span>
              </div>
            </button>
          );
        },
      },
      {
        id: "badges",
        header: "Profile",
        cell: (ctx) => {
          const row = ctx.row.original;
          const items: string[] = [];
          if (row.copyability_tier) items.push(`Tier: ${row.copyability_tier}`);
          if (row.risk_score != null) items.push(`Risk: ${row.risk_score.toFixed(1)}`);
          return <CreatorBadges items={items} />;
        },
        size: 160,
      },
      {
        id: "trades_24h",
        header: "Trades 24h",
        accessorKey: "trades_24h",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtInt(ctx.getValue())}
          </span>
        ),
      },
      {
        id: "trades_7d",
        header: "Trades 7d",
        accessorKey: "trades_7d",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtInt(ctx.getValue())}
          </span>
        ),
      },
      {
        id: "trades_30d",
        header: "Trades 30d",
        accessorKey: "trades_30d",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtInt(ctx.getValue())}
          </span>
        ),
      },
      {
        id: "exec_7d",
        header: "Exec score 7d",
        accessorKey: "avg_execution_score_7d",
        cell: (ctx) => (
          <ExecutionScoreBadge score={Number(ctx.getValue() ?? 0)} />
        ),
        size: 120,
      },
      {
        id: "roi_7d",
        header: "ROI me 7d",
        accessorKey: "roi_me_7d",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {formatPct(ctx.getValue())}
          </span>
        ),
      },
      {
        id: "exec_30d",
        header: "Exec score 30d",
        accessorKey: "avg_execution_score_30d",
        cell: (ctx) => (
          <ExecutionScoreBadge score={Number(ctx.getValue() ?? 0)} />
        ),
        size: 120,
      },
      {
        id: "roi_30d",
        header: "ROI me 30d",
        accessorKey: "roi_me_30d",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {formatPct(ctx.getValue())}
          </span>
        ),
      },
      {
        id: "last_activity",
        header: "Last activity",
        accessorKey: "last_activity",
        cell: (ctx) => (
          <span className="text-xs text-muted-foreground">
            {fmtDateTime(ctx.getValue())}
          </span>
        ),
      },
    ],
    [router]
  );

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-3">
        <PageHeader
          title="Creator Directory"
          subtitle="Ranked view of all tracked creators with execution and risk metrics."
        />

        <div className="flex items-center justify-between gap-2 text-xs">
          <div className="text-muted-foreground">
            {rows.length > 0
              ? `Tracking ${rows.length.toLocaleString()} creators`
              : "No creators found yet"}
          </div>
          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium bg-background hover:bg-accent"
          >
            Refresh
          </button>
        </div>

        <div className="border rounded-2xl bg-card">
          {isError && (
            <div className="p-4 text-sm text-red-500">
              Failed to load creators.
            </div>
          )}

          {isLoading && !rows.length && !isError && (
            <div className="p-6 text-sm text-muted-foreground">
              Loading creators…
            </div>
          )}

          {!isLoading && !rows.length && !isError && (
            <div className="p-6 text-sm text-muted-foreground">
              No creator data available yet. Once trades are ingested and
              analyzed, creators will appear here with their metrics.
            </div>
          )}

          {rows.length > 0 && (
            <DataGrid<CatalogItem>
              data={rows}
              columns={columns}
              pageSize={20}
              emptyLabel="No creators for this filter."
            />
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

function shortKey(pk: string, len = 4) {
  if (!pk) return "—";
  return `${pk.slice(0, len)}…${pk.slice(-len)}`;
}

function formatPct(v: unknown): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toFixed(1)}%`;
}
