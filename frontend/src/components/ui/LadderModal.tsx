"use client";

import * as React from "react";
import { LadderVisual } from "@/components/ladder/ladder-visual";
import type { LadderResponse } from "@/lib/types";

type Props = {
  ladder: LadderResponse | null;
  open: boolean;
  onClose: () => void;
};

export default function LadderModal({ ladder, open, onClose }: Props) {
  if (!open || !ladder) return null;

  const crowd = (ladder as any).crowding ?? {};
  const slots = (crowd.copies_per_slot ?? []) as any[];

  const visualData = slots.map((s) => ({
    relative: Number(s.relative ?? s.slot ?? 0),
    copies: Number(s.copies ?? 0),
    sources: Number(s.sources ?? s.source_count ?? 0),
  }));

  const badges: string[] = ladder.badges ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl border bg-popover shadow-xl">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="space-y-1">
            <div className="text-sm font-semibold">
              Ladder analysis · pair #{ladder.pair_id}
            </div>
            <div className="text-[11px] text-muted-foreground">
              {ladder.token_mint ? `Token: ${ladder.token_mint}` : null}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {badges.map((b) => (
              <span
                key={b}
                className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[11px]"
              >
                {b}
              </span>
            ))}
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
            >
              Close
            </button>
          </div>
        </div>

        <div className="px-4 py-3 space-y-4 overflow-y-auto max-h-[calc(90vh-52px)]">
          <div className="rounded-2xl border bg-card p-3">
            <LadderVisual data={visualData} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <StatCard
              label="Side"
              value={(ladder.side || "UNKNOWN").toString()}
            />
            <StatCard label="Window" value={`${ladder.window} slots`} />
            <StatCard
              label="ΔSlots"
              value={
                ladder.delta_slots != null
                  ? ladder.delta_slots.toString()
                  : "—"
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border bg-background px-3 py-2">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 text-xs font-semibold">{value}</div>
    </div>
  );
}
