"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { LadderResponse } from "@/lib/types";
import { LadderVisual } from "@/components/ladder/ladder-visual";

export default function LadderPage() {
  const sp = useSearchParams();
  const router = useRouter();

  // Read query params
  const initialPair = sp.get("pair_id") || "";
  const initialWin = Number(sp.get("window") || "8");

  const [pairId, setPairId] = React.useState<string>(initialPair);
  const [windowSlots, setWindowSlots] = React.useState<number>(
    Number.isFinite(initialWin) ? initialWin : 8
  );

  // Fetch ladder data
  const { data, isLoading, error, refetch } = useQuery<LadderResponse>({
    queryKey: ["ladder", pairId, windowSlots],
    queryFn: () => api.getLadder(pairId, windowSlots),
    enabled: Boolean(pairId),
    refetchInterval: 20_000, // keep fresh while user is on page
  });

  // Sync URL when user submits
  function onApply(e: React.FormEvent) {
    e.preventDefault();
    const qs = new URLSearchParams();
    if (pairId) qs.set("pair_id", pairId);
    if (windowSlots) qs.set("window", String(windowSlots));
    router.replace(`/ladder?${qs.toString()}`);
    refetch();
  }

  // Map ladder buckets to simple visual shape
  const bars =
    data?.crowding?.copies_per_slot?.map((b) => ({
      relative: b.relative,
      copies: b.copies,
      sources: b.sources,
    })) ?? [];

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-4">Ladder Analysis</h1>

      {/* Controls */}
      <form onSubmit={onApply} className="mb-4 grid gap-3 max-w-xl">
        <div className="grid md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Pair / Trade Id</label>
            <input
              className="mt-1 w-full rounded-md border bg-background px-3 py-1.5 text-sm"
              placeholder="e.g. 12345"
              value={pairId}
              onChange={(e) => setPairId(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Window (slots)</label>
            <input
              type="number"
              min={2}
              max={64}
              className="mt-1 w-full rounded-md border bg-background px-3 py-1.5 text-sm"
              value={windowSlots}
              onChange={(e) => setWindowSlots(parseInt(e.target.value || "8", 10))}
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              className="px-3 py-2 rounded-md bg-primary text-primary-foreground text-sm"
            >
              Apply
            </button>
          </div>
        </div>
      </form>

      {/* Loading / Error */}
      {isLoading && <div>Loading…</div>}
      {error && (
        <div className="text-destructive">
          Failed to load ladder. <button className="underline" onClick={() => refetch()}>Retry</button>
        </div>
      )}

      {/* Summary */}
      {data && (
        <div className="grid gap-3 mb-4 md:grid-cols-3">
          <Kpi label="Window" value={`${data.window} slots`} />
          <Kpi
            label="Crowding"
            value={`${data.crowding?.ahead ?? 0} ahead · ${data.crowding?.at_event ?? 0} at · ${data.crowding?.behind ?? 0} behind`}
          />
          <Kpi label="Total Copies" value={data.crowding?.total ?? 0} />
        </div>
      )}

      {/* Visual */}
      {bars.length > 0 ? (
        <LadderVisual data={bars} />
      ) : (
        !isLoading && pairId && (
          <div className="border border-dashed rounded-2xl p-8 text-center text-muted-foreground">
            No ladder buckets returned for this query.
          </div>
        )
      )}

      {/* Diagnostics (optional lightweight view) */}
      {data?.efficiency?.notes?.length ? (
        <div className="mt-4 border rounded-2xl p-4">
          <div className="font-medium mb-2">Notes</div>
          <ul className="list-disc pl-5 text-sm text-muted-foreground">
            {data.efficiency.notes.map((n, i) => (
              <li key={i}>{n}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="border rounded-2xl p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold mt-1">{value ?? "—"}</div>
    </div>
  );
}
