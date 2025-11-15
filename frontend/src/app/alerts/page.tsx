"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import DashboardShell from "@/components/layouts/dashboard-shell";
import { PageHeader } from "@/components/layouts/page-header";
import {
  AlertFilters,
  type AlertFiltersValue,
} from "@/components/alerts/AlertFilters";
import { AlertCard, type AlertCardProps } from "@/components/alerts/AlertCard";
import { api } from "@/lib/api";

type AlertRow = AlertCardProps["a"];

const DEFAULT_FILTERS: AlertFiltersValue = {
  q: "",
  severity: "ALL",
  resolved: "NO",
  pageSize: 50,
};

export default function AlertsPage() {
  const [filters, setFilters] = React.useState<AlertFiltersValue>(DEFAULT_FILTERS);
  const [selectedAlert, setSelectedAlert] = React.useState<AlertRow | null>(null);

  const { data, isLoading, isError, refetch } = useQuery<AlertRow[]>({
    queryKey: ["alerts", filters],
    queryFn: async () => {
      const params = buildAlertParams(filters);
      const res = await api.getAlerts(params); // ✅ uses your existing helper
      return res.items as AlertRow[];
    },
    refetchInterval: 15000,
  });

  const alerts = data ?? [];

  const openCount = alerts.filter(
    (a) => (a as any).resolved !== true && (a as any).status !== "RESOLVED"
  ).length;

  const criticalCount = alerts.filter(
    (a) => (a.severity || "").toUpperCase() === "CRITICAL"
  ).length;

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-4">
        <PageHeader
          title="Alerts"
          subtitle="Automated signals fired by rules across wallets, creators, and trades."
        />

        {/* Summary row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <SummaryCard
            label="Open alerts"
            value={openCount}
            tone={openCount > 0 ? "warn" : "ok"}
          />
          <SummaryCard
            label="Critical alerts"
            value={criticalCount}
            tone={criticalCount > 0 ? "error" : "ok"}
          />
          <SummaryCard label="Total alerts" value={alerts.length} />
          <SummaryCard
            label="Filter"
            value={`${filters.resolved} · ${filters.severity}`}
          />
        </div>

        {/* Filters + refresh */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <AlertFilters
            value={filters}
            onChange={(next) =>
              setFilters((prev) => ({
                ...prev,
                ...next,
              }))
            }
            onApply={() => refetch()}
            onReset={() => {
              setFilters(DEFAULT_FILTERS);
              refetch();
            }}
          />

          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium bg-background hover:bg-accent"
          >
            Refresh
          </button>
        </div>

        {/* List of alerts */}
        <div className="space-y-2">
          {isError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-red-500">
              Failed to load alerts.
            </div>
          )}

          {isLoading && !alerts.length && !isError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              Loading alerts…
            </div>
          )}

          {!isLoading && !alerts.length && !isError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              No alerts for this filter. Once rules trigger, they will appear here.
            </div>
          )}

          {alerts.map((alert) => (
            <button
              key={alert.id ?? alert.trade_id ?? String(Math.random())}
              type="button"
              onClick={() => setSelectedAlert(alert)}
              className="w-full text-left"
            >
              {/* ✅ AlertCard expects prop `a`, not `alert` */}
              <AlertCard a={alert} />
            </button>
          ))}
        </div>

        {/* Detail modal can be wired back in later, once types are aligned */}
        {/* {selectedAlert && (
          <AlertDetailModal
            alert={selectedAlert}
            open={!!selectedAlert}
            onClose={() => setSelectedAlert(null)}
          />
        )} */}
      </div>
    </DashboardShell>
  );
}

/** Map our AlertFiltersValue into the query arg expected by api.getAlerts */
function buildAlertParams(filters: AlertFiltersValue): Record<string, any> {
  const params: Record<string, any> = {};
  if (filters.q) params.q = filters.q;
  if (filters.severity && filters.severity !== "ALL") {
    params.severity = filters.severity;
  }
  if (filters.resolved && filters.resolved !== "ALL") {
    // backend can interpret resolved=YES/NO however it likes; we’re just forwarding
    params.resolved = filters.resolved;
  }
  if (filters.pageSize) {
    params.page_size = filters.pageSize;
  }
  return params;
}

function SummaryCard({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number | string;
  tone?: "ok" | "warn" | "error" | "neutral";
}) {
  const base =
    "rounded-2xl border bg-card px-3 py-2 flex flex-col justify-between";
  const toneClasses =
    tone === "ok"
      ? ""
      : tone === "warn"
      ? "border-amber-500/40 bg-amber-500/5"
      : tone === "error"
      ? "border-red-500/40 bg-red-500/5"
      : "";

  return (
    <div className={`${base} ${toneClasses}`}>
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
    </div>
  );
}
