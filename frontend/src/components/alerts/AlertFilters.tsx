"use client";

import * as React from "react";

export type AlertFiltersValue = {
  q: string;
  severity: "ALL" | "INFO" | "WARN" | "CRITICAL";
  resolved: "ALL" | "YES" | "NO";
  pageSize: number;
};

export function AlertFilters({
  value,
  onChange,
  onApply,
  onReset,
}: {
  value: AlertFiltersValue;
  onChange: (next: Partial<AlertFiltersValue>) => void;
  onApply: () => void;
  onReset: () => void;
}) {
  const PAGE_SIZES = [10, 20, 50];

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onApply();
      }}
      className="mb-3 grid gap-3"
    >
      <div className="grid md:grid-cols-4 gap-3">
        <div>
          <label className="text-xs text-muted-foreground">Search</label>
          <input
            className="mt-1 w-full rounded-md border bg-background px-3 py-1.5 text-sm"
            placeholder="reason, category…"
            value={value.q}
            onChange={(e) => onChange({ q: e.target.value })}
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Severity</label>
          <select
            className="mt-1 w-full rounded-md border bg-background px-3 py-1.5 text-sm"
            value={value.severity}
            onChange={(e) =>
              onChange({ severity: e.target.value as any })
            }
          >
            <option value="ALL">All</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warn</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Resolved</label>
          <select
            className="mt-1 w-full rounded-md border bg-background px-3 py-1.5 text-sm"
            value={value.resolved}
            onChange={(e) =>
              onChange({ resolved: e.target.value as any })
            }
          >
            <option value="ALL">All</option>
            <option value="YES">Yes</option>
            <option value="NO">No</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Page size</label>
          <select
            className="mt-1 w-full rounded-md border bg-background px-3 py-1.5 text-sm"
            value={value.pageSize}
            onChange={(e) =>
              onChange({ pageSize: parseInt(e.target.value, 10) })
            }
          >
            {PAGE_SIZES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          className="px-3 py-1.5 rounded-md bg-primary text-primary-foreground text-sm"
        >
          Apply
        </button>
        <button
          type="button"
          onClick={onReset}
          className="px-3 py-1.5 rounded-md border text-sm"
        >
          Reset
        </button>
      </div>
    </form>
  );
}
