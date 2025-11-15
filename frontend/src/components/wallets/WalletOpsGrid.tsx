"use client";

import * as React from "react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataGrid } from "@/components/tables/data-grid";
import { ExecutionScoreBadge } from "@/components/ui/ExecutionScoreBadge";
import { fmtInt, fmtNum } from "@/components/tables/column-helpers";
import type { WalletOpsRow } from "@/lib/api";

type Props = {
  rows: WalletOpsRow[];
  onSelectWallet?: (row: WalletOpsRow) => void;
};

export default function WalletOpsGrid({ rows, onSelectWallet }: Props) {
  const columns = React.useMemo<ColumnDef<WalletOpsRow, any>[]>(
    () => [
      {
        id: "wallet",
        header: "Wallet",
        accessorKey: "id",
        cell: (ctx) => {
          const row = ctx.row.original;
          return (
            <button
              type="button"
              onClick={() => onSelectWallet?.(row)}
              className="text-left"
            >
              <div className="flex flex-col">
                <span className="text-sm font-semibold">
                  {row.label || "Wallet"}
                </span>
                <span className="font-mono text-[11px] text-muted-foreground">
                  {row.id}
                </span>
              </div>
            </button>
          );
        },
      },
      {
        id: "state",
        header: "State",
        accessorKey: "state",
        cell: (ctx) => (
          <span className="text-xs uppercase">
            {String(ctx.getValue() || "UNKNOWN")}
          </span>
        ),
      },
      {
        id: "pnl",
        header: "PnL (SOL)",
        accessorKey: "total_pnl_sol",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtNum(ctx.getValue(), 3)}
          </span>
        ),
      },
      {
        id: "roi",
        header: "ROI %",
        accessorKey: "roi_pct",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtNum(ctx.getValue(), 1)}
          </span>
        ),
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
        id: "alerts_open",
        header: "Open alerts",
        accessorKey: "alerts_open",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtInt(ctx.getValue())}
          </span>
        ),
      },
      {
        id: "exec_7d",
        header: "Exec score 7d",
        accessorKey: "avg_exec_score_7d",
        cell: (ctx) => (
          <ExecutionScoreBadge
            score={
              typeof ctx.getValue() === "number"
                ? (ctx.getValue() as number)
                : null
            }
          />
        ),
      },
    ],
    [onSelectWallet]
  );

  return (
    <DataGrid<WalletOpsRow>
      data={rows}
      columns={columns}
      pageSize={20}
      emptyLabel="No wallets."
    />
  );
}
