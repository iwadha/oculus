"use client";

import * as React from "react";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { cn } from "@/lib/utils";

export type DataGridProps<TData extends object> = {
  data: TData[];
  columns: ColumnDef<TData, any>[];

  /** Client-side pagination (optional). If omitted, we render all rows. */
  pageSize?: number;
  className?: string;

  /** Optional initial sort: [{ id: "field", desc: false }] */
  initialSorting?: SortingState;
  emptyLabel?: string;
};

export function DataGrid<TData extends object>({
  data,
  columns,
  pageSize = 20,
  className,
  initialSorting = [],
  emptyLabel = "No rows.",
}: DataGridProps<TData>) {
  const [sorting, setSorting] = React.useState<SortingState>(initialSorting);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: { pageIndex: 0, pageSize },
    },
  });

  const headerGroups = table.getHeaderGroups();
  const rowModel = table.getRowModel();

  return (
    <div className={cn("border rounded-2xl overflow-hidden", className)}>
      <table className="w-full text-sm">
        <thead className="bg-muted text-muted-foreground">
          {headerGroups.map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => {
                const isSortable = header.column.getCanSort();
                const sortDir = header.column.getIsSorted() as false | "asc" | "desc";
                return (
                  <th
                    key={header.id}
                    className={cn("p-2 text-left select-none", isSortable && "cursor-pointer")}
                    onClick={isSortable ? header.column.getToggleSortingHandler() : undefined}
                  >
                    <span className="inline-flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {isSortable && <SortIcon dir={sortDir} />}
                    </span>
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {rowModel.rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="p-4 text-center text-muted-foreground">
                {emptyLabel}
              </td>
            </tr>
          ) : (
            rowModel.rows.map((row) => (
              <tr key={row.id} className="border-t border-border">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="p-2 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="flex items-center justify-between p-2">
        <div className="text-xs text-muted-foreground">
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount() || 1}
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-1.5 rounded-md border text-sm disabled:opacity-50"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Prev
          </button>
          <button
            className="px-3 py-1.5 rounded-md border text-sm disabled:opacity-50"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------- small UI ---------- */

function SortIcon({ dir }: { dir: false | "asc" | "desc" }) {
  if (!dir)
    return (
      <svg width="10" height="10" viewBox="0 0 20 20" aria-hidden className="opacity-40">
        <path d="M7 7h6M5 10h10M3 13h14" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
    );
  if (dir === "asc")
    return (
      <svg width="10" height="10" viewBox="0 0 20 20" aria-hidden>
        <path d="M10 6l-4 6h8l-4-6z" fill="currentColor" />
      </svg>
    );
  return (
    <svg width="10" height="10" viewBox="0 0 20 20" aria-hidden>
      <path d="M10 14l4-6H6l4 6z" fill="currentColor" />
    </svg>
  );
}
