"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { CompareResponse } from "@/lib/types";

export default function ComparePage() {
  const sp = useSearchParams();
  const router = useRouter();
  const tradeId = sp.get("trade_id") || "";

  const {
    data,
    isLoading,
    refetch,
    error,
  } = useQuery<CompareResponse>({
    queryKey: ["compare", tradeId],
    queryFn: () => api.getCompare(tradeId),
    enabled: !!tradeId,
  });

  // No trade_id provided
  if (!tradeId) {
    return (
      <div className="p-4 max-w-3xl mx-auto">
        <button
          className="mb-3 px-3 py-1.5 rounded bg-muted"
          onClick={() => router.back()}
        >
          Back
        </button>
        <h1 className="text-xl font-semibold mb-2">Transaction Comparison</h1>
        <p className="text-sm text-muted-foreground">
          Provide a <code>trade_id</code> in the URL, e.g.&nbsp;
          <code className="font-mono">
            /compare?trade_id=YOUR_TRADE_ID
          </code>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <button
        className="mb-3 px-3 py-1.5 rounded bg-muted"
        onClick={() => router.back()}
      >
        Back
      </button>

      <h1 className="text-xl font-semibold mb-3">Transaction Comparison</h1>

      {isLoading && <div>Loading…</div>}

      {error && (
        <div className="text-destructive">
          {error instanceof Error ? error.message : "Failed to load."}{" "}
          <button className="underline" onClick={() => refetch()}>
            Retry
          </button>
        </div>
      )}

      {data && <CompareView data={data} />}
    </div>
  );
}

function CompareView({ data }: { data: CompareResponse }) {
  if ("status" in data && data.status === "AWAITING_MATCH") {
    return (
      <div className="border rounded-2xl p-4 text-sm text-muted-foreground">
        Awaiting match…
      </div>
    );
  }

  const d = data as Extract<CompareResponse, { token_mint: string }>;

  return (
    <div className="grid gap-4">
      <div className="grid grid-cols-2 gap-3">
        <Kpi label="ΔSlots" value={d.deltas.slots} />
        <Kpi label="Price Drift %" value={d.deltas.price_drift_pct ?? null} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <KVCard title="Copy Trade" obj={d.copy} />
        <KVCard title="Source Trade" obj={d.source} />
      </div>

      <div>
        <a
          className="px-3 py-1.5 inline-block rounded bg-primary text-primary-foreground"
          href={`/ladder?pair_id=${encodeURIComponent(d.copy.trade_id)}`}
        >
          Open in Ladder
        </a>
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
