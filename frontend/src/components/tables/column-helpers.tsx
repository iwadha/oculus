import * as React from "react";
import type { ColumnDef, SortingFnOption } from "@tanstack/react-table";

/**
 * Common formatters
 */
export function fmtInt(v: unknown): string {
  const n = Number(v);
  return Number.isFinite(n) ? new Intl.NumberFormat().format(Math.round(n)) : "—";
}

export function fmtNum(v: unknown, dp = 2): string {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(dp) : "—";
}

export function fmtPct(v: unknown, dp = 1): string {
  const n = Number(v);
  return Number.isFinite(n) ? `${n.toFixed(dp)}%` : "—";
}

export function fmtDateTime(v: unknown): string {
  if (!v) return "—";
  try {
    return new Date(String(v)).toLocaleString();
  } catch {
    return "—";
  }
}

export function hashShort(v: unknown, head = 6, tail = 4): string {
  if (!v) return "—";
  const s = String(v);
  if (s.length <= head + tail + 1) return s;
  return `${s.slice(0, head)}…${s.slice(-tail)}`;
}

/**
 * Reusable sorting helpers (optional)
 */
export const sortNumeric: SortingFnOption<any> = (rowA, rowB, colId) => {
  const a = Number(rowA.getValue(colId));
  const b = Number(rowB.getValue(colId));
  if (Number.isNaN(a) && Number.isNaN(b)) return 0;
  if (Number.isNaN(a)) return 1;
  if (Number.isNaN(b)) return -1;
  return a < b ? -1 : a > b ? 1 : 0;
};

/**
 * Column factory helpers
 */

export function colText<T extends object>(
  key: keyof T & string,
  header: string,
  opts: Partial<ColumnDef<T, any>> = {}
): ColumnDef<T, any> {
  return {
    id: key,
    accessorKey: key,
    header,
    cell: (ctx) => String(ctx.getValue() ?? "—"),
    ...opts,
  };
}

export function colMono<T extends object>(
  key: keyof T & string,
  header: string,
  opts: Partial<ColumnDef<T, any>> = {}
): ColumnDef<T, any> {
  return {
    id: key,
    accessorKey: key,
    header,
    cell: (ctx) => <span className="font-mono">{String(ctx.getValue() ?? "—")}</span>,
    ...opts,
  };
}

export function colHash<T extends object>(
  key: keyof T & string,
  header: string,
  opts: Partial<ColumnDef<T, any>> = {}
): ColumnDef<T, any> {
  return {
    id: key,
    accessorKey: key,
    header,
    cell: (ctx) => {
      const v = ctx.getValue();
      const s = hashShort(v);
      return (
        <span className="font-mono" title={String(v ?? "")}>
          {s}
        </span>
      );
    },
    ...opts,
  };
}

export function colNumber<T extends object>(
  key: keyof T & string,
  header: string,
  dp = 2,
  opts: Partial<ColumnDef<T, any>> = {}
): ColumnDef<T, any> {
  return {
    id: key,
    accessorKey: key,
    header,
    sortingFn: sortNumeric,
    cell: (ctx) => fmtNum(ctx.getValue(), dp),
    ...opts,
  };
}

export function colPercent<T extends object>(
  key: keyof T & string,
  header: string,
  dp = 1,
  opts: Partial<ColumnDef<T, any>> = {}
): ColumnDef<T, any> {
  return {
    id: key,
    accessorKey: key,
    header,
    sortingFn: sortNumeric,
    cell: (ctx) => fmtPct(ctx.getValue(), dp),
    ...opts,
  };
}

export function colDateTime<T extends object>(
  key: keyof T & string,
  header: string,
  opts: Partial<ColumnDef<T, any>> = {}
): ColumnDef<T, any> {
  return {
    id: key,
    accessorKey: key,
    header,
    cell: (ctx) => fmtDateTime(ctx.getValue()),
    ...opts,
  };
}
