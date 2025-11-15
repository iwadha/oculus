"use client";

import * as React from "react";
import Link from "next/link";
import { ExecutionScoreBadge } from "@/components/ui/ExecutionScoreBadge";

/**
 * Generic activity table for a creator.
 * `rows` may come directly from your /creators/:pubkey/activity endpoint.
 * We defensively read common fields and render gracefully if missing.
 */
export function CreatorActivityTable({ rows }: { rows: any[] }) {
  const list = Array.isArray(rows) ? rows : [];

  return (
    <div className="border rounded-2xl overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted text-muted-foreground">
          <tr>
            <Th>Time</Th>
            <Th>Action</Th>
            <Th>Token</Th>
            <Th>Amount</Th>
            <Th>Price</Th>
            <Th>Exec</Th>
            <Th>ΔSlots</Th>
            <Th></Th>
          </tr>
        </thead>
        <tbody>
          {!list.length ? (
            <tr>
              <td className="p-4 text-center text-muted-foreground" colSpan={8}>
                No recent activity.
              </td>
            </tr>
          ) : (
            list.map((r, i) => {
              const ts =
                r.ts || r.time || r.created_at || r.block_time || null;
              const action = (r.action || r.side || "").toString().toUpperCase();
              const token = r.token || r.mint || r.symbol || "—";
              const amt =
                r.amount ??
                r.size ??
                r.qty ??
                r.quantity ??
                null;
              const price =
                r.price ??
                r.avg_price ??
                r.execution_price ??
                null;
              const score =
                r.execution_score ??
                r.exec_score ??
                null;
              const delta =
                (r.copy_slot ?? 0) - (r.source_slot ?? 0);

              const tradeId =
                r.trade_id ?? r.id ?? null;

              return (
                <tr key={i} className="border-t border-border">
                  <Td>{ts ? new Date(ts).toLocaleString() : "—"}</Td>
                  <Td>
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        action === "BUY"
                          ? "bg-emerald-900/40 text-emerald-300"
                          : action === "SELL"
                          ? "bg-rose-900/40 text-rose-300"
                          : "bg-muted"
                      }`}
                    >
                      {action || "—"}
                    </span>
                  </Td>
                  <Td className="font-mono">{token}</Td>
                  <Td>{amt == null ? "—" : fmtNum(amt)}</Td>
                  <Td>{price == null ? "—" : fmtNum(price)}</Td>
                  <Td>
                    <ExecutionScoreBadge score={typeof score === "number" ? score : null} />
                  </Td>
                  <Td>{Number.isFinite(delta) ? delta : "—"}</Td>
                  <Td>
                    <div className="flex gap-2">
                      {tradeId && (
                        <Link
                          className="text-xs underline"
                          href={`/compare?trade_id=${encodeURIComponent(tradeId)}`}
                        >
                          Compare
                        </Link>
                      )}
                      {tradeId && (
                        <Link
                          className="text-xs underline"
                          href={`/ladder?pair_id=${encodeURIComponent(tradeId)}`}
                        >
                          Ladder
                        </Link>
                      )}
                    </div>
                  </Td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="text-left p-2">{children ?? null}</th>;
}
function Td({
  children,
  className = "",
}: {
  children?: React.ReactNode;
  className?: string;
}) {
  return <td className={`p-2 ${className}`}>{children ?? null}</td>;
}
function fmtNum(n: number, dp = 4) {
  try {
    const x = Number(n);
    if (!Number.isFinite(x)) return "—";
    return x.toFixed(dp);
  } catch {
    return "—";
  }
}
