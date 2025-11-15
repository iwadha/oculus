"use client";

import * as React from "react";
import Link from "next/link";
import type { ColumnDef } from "@tanstack/react-table";

import { DataGrid } from "@/components/tables/data-grid";
import {
  fmtDateTime,
  fmtNum,
  hashShort,
} from "@/components/tables/column-helpers";
import { ExecutionScoreBadge } from "@/components/ui/ExecutionScoreBadge";

export type TradeRow = {
  id: string;
  timestamp?: string | number | Date | null;
  side?: "BUY" | "SELL" | string | null;
  token_symbol?: string | null;
  size_sol?: number | null;
  price_sol?: number | null;
  pnl_sol?: number | null;
  exec_score?: number | null;
  creator_pubkey?: string | null;
  wallet_id?: string | null;
};

type Props = {
  rows: any[]; // raw rows from /v1/trades
  pageSize?: number;
};

export default function LiveTradesTable({ rows, pageSize = 20 }: Props) {
  const data = React.useMemo<TradeRow[]>(() => rows.map(normalizeTradeRow), [rows]);

  const columns = React.useMemo<ColumnDef<TradeRow, any>[]>(
    () => [
      {
        id: "time",
        header: "Time",
        accessorKey: "timestamp",
        cell: (ctx) => fmtDateTime(ctx.getValue()),
      },
      {
        id: "side",
        header: "Side",
        accessorKey: "side",
        cell: (ctx) => {
          const v = String(ctx.getValue() ?? "").toUpperCase();
          const tone =
            v === "BUY"
              ? "bg-emerald-900/40 text-emerald-300"
              : v === "SELL"
              ? "bg-rose-900/40 text-rose-300"
              : "bg-muted text-muted-foreground";
          return (
            <span className={`px-2 py-0.5 rounded text-xs ${tone}`}>
              {v || "—"}
            </span>
          );
        },
      },
      {
        id: "token",
        header: "Token",
        accessorKey: "token_symbol",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {ctx.getValue() || "—"}
          </span>
        ),
      },
      {
        id: "size",
        header: "Size (SOL)",
        accessorKey: "size_sol",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtNum(ctx.getValue(), 4)}
          </span>
        ),
      },
      {
        id: "price",
        header: "Price (SOL)",
        accessorKey: "price_sol",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtNum(ctx.getValue(), 6)}
          </span>
        ),
      },
      {
        id: "pnl",
        header: "PnL (SOL)",
        accessorKey: "pnl_sol",
        cell: (ctx) => (
          <span className="font-mono text-xs">
            {fmtNum(ctx.getValue(), 4)}
          </span>
        ),
      },
      {
        id: "exec",
        header: "Exec",
        accessorKey: "exec_score",
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
      {
        id: "creator",
        header: "Creator",
        accessorKey: "creator_pubkey",
        cell: (ctx) => {
          const v = ctx.getValue() as string | null | undefined;
          if (!v) return "—";
          return (
            <Link
              href={`/creators/${encodeURIComponent(v)}`}
              className="underline font-mono text-xs"
            >
              {hashShort(v)}
            </Link>
          );
        },
      },
      {
        id: "wallet",
        header: "Wallet",
        accessorKey: "wallet_id",
        cell: (ctx) => {
          const v = ctx.getValue() as string | null | undefined;
          if (!v) return "—";
          return (
            <span className="font-mono text-[11px] text-muted-foreground">
              {hashShort(v)}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: "",
        cell: (ctx) => {
          const r = ctx.row.original;
          return (
            <div className="flex gap-2">
              <Link
                className="text-xs underline"
                href={`/compare?trade_id=${encodeURIComponent(r.id)}`}
              >
                Compare
              </Link>
              <Link
                className="text-xs underline"
                href={`/ladder?pair_id=${encodeURIComponent(r.id)}`}
              >
                Ladder
              </Link>
            </div>
          );
        },
      },
    ],
    []
  );

  return (
    <DataGrid<TradeRow>
      data={data}
      columns={columns}
      pageSize={pageSize}
      emptyLabel="No trades."
    />
  );
}

function normalizeTradeRow(r: any): TradeRow {
  return {
    id: String(r.id ?? r.trade_id ?? r.tx_sig ?? r.signature ?? randomId()),
    timestamp:
      r.timestamp ??
      r.ts ??
      r.time ??
      r.block_time ??
      r.created_at ??
      null,
    side: (r.side ?? r.action ?? "").toUpperCase(),
    token_symbol: r.token_symbol ?? r.symbol ?? r.mint ?? null,
    size_sol: r.size_sol ?? r.size ?? r.amount ?? null,
    price_sol: r.price_sol ?? r.price ?? r.execution_price ?? null,
    pnl_sol: r.pnl_sol ?? r.pnl ?? null,
    exec_score: r.exec_score ?? r.execution_score ?? null,
    creator_pubkey: r.creator_pubkey ?? r.creator ?? null,
    wallet_id: r.wallet_id ?? r.wallet ?? null,
  };
}

function randomId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return (crypto as any).randomUUID();
  }
  return Math.random().toString(36).slice(2);
}
