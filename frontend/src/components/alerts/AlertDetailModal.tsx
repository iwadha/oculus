"use client";

import * as React from "react";

type Props = {
  alert: any; // relaxed for now
  open: boolean;
  onClose: () => void;
};

export default function AlertDetailModal({ alert, open, onClose }: Props) {
  if (!open || !alert) return null;

  const severity = String(alert.severity || "").toUpperCase();
  const status = String(alert.status || "OPEN").toUpperCase();

  const severityTone =
    severity === "CRITICAL"
      ? "bg-red-500/10 text-red-400"
      : severity === "HIGH"
      ? "bg-amber-500/10 text-amber-300"
      : "bg-zinc-700 text-zinc-200";

  const statusTone =
    status === "OPEN"
      ? "bg-emerald-500/10 text-emerald-400"
      : "bg-zinc-700 text-zinc-200";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-2xl border bg-popover shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="space-y-1">
            <div className="text-sm font-semibold">
              {alert.rule_name || alert.type || "Alert"}
            </div>
            <div className="text-[11px] text-muted-foreground">
              {alert.id}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${severityTone}`}
            >
              {severity || "UNKNOWN"}
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${statusTone}`}
            >
              {status}
            </span>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
            >
              Close
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="px-4 py-3 space-y-4 overflow-y-auto max-h-[calc(90vh-52px)]">
          {/* Reason / message */}
          <section className="space-y-1">
            <div className="text-xs font-semibold">Reason</div>
            <div className="text-sm">
              {alert.reason || alert.message || "No description provided."}
            </div>
          </section>

          {/* Context */}
          <section className="space-y-2">
            <div className="text-xs font-semibold">Context</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <ContextField
                label="Wallet"
                value={alert.wallet_label || alert.wallet_id}
              />
              <ContextField
                label="Creator"
                value={alert.creator_alias || alert.creator_id}
              />
              <ContextField label="Trade" value={alert.trade_id} mono />
              <ContextField
                label="Created at"
                value={
                  alert.created_at &&
                  new Date(alert.created_at).toLocaleString()
                }
              />
              <ContextField
                label="Resolved at"
                value={
                  alert.resolved_at &&
                  new Date(alert.resolved_at).toLocaleString()
                }
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function ContextField({
  label,
  value,
  mono,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
}) {
  return (
    <div className="rounded-2xl border bg-background px-3 py-2">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className={"mt-1 text-xs " + (mono ? "font-mono break-all" : "")}>
        {value || "—"}
      </div>
    </div>
  );
}
