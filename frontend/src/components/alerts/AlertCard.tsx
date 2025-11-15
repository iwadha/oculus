"use client";

import * as React from "react";
import Link from "next/link";
import { ExecutionScoreBadge } from "@/components/ui/ExecutionScoreBadge";

export type AlertCardProps = {
  a: {
    id?: string | number;
    created_at?: string | null;
    severity?: "INFO" | "WARN" | "CRITICAL" | null;
    title?: string | null;
    reason?: string | null;
    category?: string | null;
    trade_id?: string | null;
    wallet_id?: string | null;
    creator_pubkey?: string | null;
    execution_score?: number | null;
    // allow extra fields
    [k: string]: any;
  };
};

const sevClass: Record<string, string> = {
  INFO: "bg-blue-900/40 text-blue-300",
  WARN: "bg-amber-900/40 text-amber-300",
  CRITICAL: "bg-rose-900/40 text-rose-300",
};

export function AlertCard({ a }: AlertCardProps) {
  const created = a.created_at ? new Date(a.created_at).toLocaleString() : "—";
  const sev = (a.severity ?? "INFO") as keyof typeof sevClass;

  return (
    <div className="rounded-2xl border p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs ${sevClass[sev] ?? "bg-muted"}`}
              title="Severity"
            >
              {sev}
            </span>
            {a.category && (
              <span className="px-2 py-0.5 rounded bg-muted text-xs">
                {a.category}
              </span>
            )}
            {typeof a.execution_score === "number" && (
              <ExecutionScoreBadge score={a.execution_score} />
            )}
          </div>

          <div className="mt-2 font-medium truncate">
            {a.title ?? a.reason ?? "Alert"}
          </div>
          <div className="text-xs text-muted-foreground mt-1 truncate">
            {created}
            {a.wallet_id && (
              <>
                {" "}
                · wallet <span className="font-mono">{a.wallet_id}</span>
              </>
            )}
            {a.creator_pubkey && (
              <>
                {" "}
                · creator{" "}
                <Link
                  className="underline"
                  href={`/creators/${encodeURIComponent(a.creator_pubkey)}`}
                >
                  {a.creator_pubkey.slice(0, 6)}…{a.creator_pubkey.slice(-4)}
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          {a.trade_id && (
            <Link
              className="text-xs underline"
              href={`/compare?trade_id=${encodeURIComponent(a.trade_id)}`}
            >
              Compare trade
            </Link>
          )}
          {a.trade_id && (
            <Link
              className="text-xs underline"
              href={`/ladder?pair_id=${encodeURIComponent(a.trade_id)}`}
            >
              View ladder
            </Link>
          )}
        </div>
      </div>

      {a.details && (
        <pre className="mt-3 rounded-md bg-muted p-2 text-xs overflow-auto">
{typeof a.details === "string" ? a.details : JSON.stringify(a.details, null, 2)}
        </pre>
      )}
    </div>
  );
}
