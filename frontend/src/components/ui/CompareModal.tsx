"use client";
import * as React from "react";
import { api } from "@/lib/api";
import type { CompareResponse } from "@/lib/types";

export function CompareModal({
  tradeId,
  open,
  onClose,
}: { tradeId: string; open: boolean; onClose: () => void }) {
  const [data, setData] = React.useState<CompareResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    api
      .getCompare(tradeId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [open, tradeId]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      role="dialog"
      aria-modal
    >
      <div className="bg-background border rounded-2xl w-full max-w-3xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="font-semibold">Transaction Comparison</div>
          <button className="px-2 py-1 rounded border" onClick={onClose}>
            Close
          </button>
        </div>

        {loading && <div>Loading…</div>}
        {error && (
          <div className="text-sm text-destructive">
            Error: {error}
          </div>
        )}

        {!loading && !error && data && (
          "status" in data ? (
            <div className="text-sm text-muted-foreground">Awaiting match…</div>
          ) : (
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-3">
                <Kpi label="ΔSlots" value={data.deltas.slots} />
                <Kpi
                  label="Price Drift %"
                  value={data.deltas.price_drift_pct ?? null}
                />
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <KVCard title="Copy Trade" obj={data.copy} />
                <KVCard title="Source Trade" obj={data.source} />
              </div>

              <a
                className="px-3 py-1.5 inline-block rounded bg-primary text-primary-foreground w-fit"
                href={`/ladder?pair_id=${encodeURIComponent(data.copy.trade_id)}`}
              >
                Open in Ladder
              </a>
            </div>
          )
        )}
      </div>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: any }) {
  return (
    <div className="border rounded-2xl p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold">{value ?? "—"}</div>
    </div>
  );
}

function KVCard({ title, obj }: { title: string; obj: Record<string, any> }) {
  return (
    <div className="border rounded-2xl p-4">
      <div className="font-medium mb-2">{title}</div>
      <table className="w-full text-sm">
        <tbody>
          {Object.entries(obj).map(([k, v]) => (
            <tr key={k}>
              <td className="py-1 text-muted-foreground pr-4">{k}</td>
              <td className="py-1 font-mono">{String(v)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
