"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import DashboardShell from "@/components/layouts/dashboard-shell"; // adjust
import { PageHeader } from "@/components/layouts/page-header"; // adjust
import { api } from "@/lib/api";
import type { SystemStatus, SystemMetrics } from "@/lib/api";
import { SystemHealthCard } from "@/components/dashboard/SystemHealthCard";
import { SystemMetricsGrid } from "@/components/dashboard/SystemMetricsGrid";
import { RecentTradesCard } from "@/components/dashboard/RecentTradesCard";

export default function DashboardPage() {
  const {
    data: status,
    isLoading: statusLoading,
    isError: statusError,
  } = useQuery<SystemStatus>({
    queryKey: ["system-status"],
    queryFn: () => api.getSystemStatus(),
    refetchInterval: 15000,
  });

  const {
    data: metrics,
    isLoading: metricsLoading,
    isError: metricsError,
  } = useQuery<SystemMetrics>({
    queryKey: ["system-metrics"],
    queryFn: () => api.getSystemMetrics(),
    refetchInterval: 15000,
  });

  const anyError = statusError || metricsError;

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-4">
        <PageHeader
          title="Oculus Command Center"
          subtitle="Live view of system health, throughput, and trading activity."
        />

        {anyError && (
          <div className="rounded-2xl border border-amber-500/40 bg-amber-500/5 px-3 py-2 text-xs text-amber-200">
            Some system diagnostics failed to load. Backend might still be
            starting up.
          </div>
        )}

        {/* Row 1: Health + Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.2fr),minmax(0,2fr)] gap-3">
          <SystemHealthCard status={status} />
          <SystemMetricsGrid metrics={metrics} />
        </div>

        {/* Row 2: Recent Trades */}
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr),minmax(0,1fr)] gap-3">
          <RecentTradesCard />
          {/* Placeholder for future: Top Creators / Wallet Health */}
          <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
            <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
              Coming soon
            </div>
            <div>Top creators, wallet health, and risk panels will live here.</div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
