"use client";

import * as React from "react";

export function CreatorHeader({
  alias,
  pubkey,
  badges = [],
}: {
  alias?: string | null;
  pubkey: string;
  badges?: string[];
}) {
  function copy() {
    navigator.clipboard.writeText(pubkey).catch(() => {});
  }

  return (
    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div className="min-w-0">
        <div className="text-xl font-semibold truncate">
          {alias || "Creator"}
        </div>
        <div className="text-xs text-muted-foreground flex items-center gap-2">
          <span className="font-mono truncate">{pubkey}</span>
          <button
            onClick={copy}
            className="px-2 py-0.5 rounded-md border hover:bg-muted"
            title="Copy pubkey"
          >
            Copy
          </button>
        </div>
      </div>

      {!!badges.length && (
        <div className="flex flex-wrap gap-2">
          {badges.map((b, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded bg-muted text-xs whitespace-nowrap"
            >
              {b}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
