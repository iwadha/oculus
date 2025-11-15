"use client";

import * as React from "react";
import { ExecutionScoreTooltip } from "./ExecutionScoreTooltip";

export function ExecutionScoreBadge({ score }: { score: number | null }) {
  if (score == null || Number.isNaN(score)) {
    return (
      <span className="px-2 py-0.5 rounded bg-muted text-xs">n/a</span>
    );
  }

  const s = Math.max(0, Math.min(100, Math.round(score)));
  const tone =
    s >= 80
      ? "bg-emerald-900/40 text-emerald-300"
      : s >= 60
      ? "bg-amber-900/40 text-amber-300"
      : s >= 40
      ? "bg-zinc-800 text-zinc-200"
      : "bg-rose-900/40 text-rose-300";

  return (
    <ExecutionScoreTooltip score={s}>
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${tone}`}>
        {s}
      </span>
    </ExecutionScoreTooltip>
  );
}
