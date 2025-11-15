"use client";

import * as React from "react";
import type { SystemStatus } from "@/lib/api";

export function SystemHealthCard({ status }: { status: SystemStatus | undefined }) {
  if (!status) {
    return (
      <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
        Loading system status…
      </div>
    );
  }

  const healthy = status.status === "ok";
  const dbOk = status.database === "connected";
  const workers = status.workers || {};

  return (
    <div className="rounded-2xl border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            System Health
          </div>
          <div className="text-sm font-semibold">
            {healthy ? "All systems nominal" : "Degraded"}
          </div>
        </div>
        <div
          className={
            "inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-medium " +
            (healthy
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-amber-500/10 text-amber-400")
          }
        >
          <span className="inline-block h-2 w-2 rounded-full bg-current" />
          {status.env} · {status.stream_source}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-xl border bg-background px-3 py-2">
          <div className="text-[11px] text-muted-foreground">Database</div>
          <div
            className={
              "mt-1 font-medium " +
              (dbOk ? "text-emerald-400" : "text-amber-400")
            }
          >
            {status.database}
          </div>
        </div>

        <div className="rounded-xl border bg-background px-3 py-2">
          <div className="text-[11px] text-muted-foreground">Workers</div>
          <div className="mt-1 flex flex-wrap gap-1">
            {Object.entries(workers).map(([name, enabled]) => (
              <span
                key={name}
                className={
                  "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] " +
                  (enabled
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-zinc-700 text-zinc-300")
                }
              >
                <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current" />
                {name.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="text-[11px] text-muted-foreground">
        Last checked:{" "}
        <span className="font-mono">
          {new Date(status.timestamp).toLocaleString()}
        </span>
      </div>
    </div>
  );
}
