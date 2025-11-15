"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import DashboardShell from "@/components/layouts/dashboard-shell";
import { PageHeader } from "@/components/layouts/page-header";
import { CreatorHeader } from "@/components/creators/CreatorHeader";           // adjust path if needed
import { CreatorKPIs } from "@/components/creators/CreatorKPIs";               // adjust path if needed
import { CreatorCharts } from "@/components/creators/CreatorCharts";           // adjust path if needed
import { CreatorActivityTable } from "@/components/creators/CreatorActivityTable"; // adjust path if needed
import { api } from "@/lib/api";

type CreatorDetailPageProps = {
  params: { pubkey: string };
};

export default function CreatorDetailPage({ params }: CreatorDetailPageProps) {
  const { pubkey } = params;

  // ---- Profile ----
  const {
    data: profile,
    isLoading: profileLoading,
    isError: profileError,
  } = useQuery<any>({
    queryKey: ["creator-profile", pubkey],
    queryFn: () => api.getCreatorProfile(pubkey),
    refetchInterval: 30000,
  });

  // ---- Activity ----
  const {
    data: activity,
    isLoading: activityLoading,
    isError: activityError,
  } = useQuery<any[]>({
    queryKey: ["creator-activity", pubkey],
    queryFn: async () => {
      // simple 1-page fetch for now; we can add pagination later
      const qs = new URLSearchParams({
        page: "1",
        page_size: "200",
      });
      return api.getCreatorActivity(pubkey, qs);
    },
    refetchInterval: 30000,
  });

  // ---- Derived view-model pieces ----

  const alias: string | null =
    profile?.alias ??
    profile?.display_name ??
    profile?.creator_alias ??
    null;

  // badges is just a string array; we pull a couple of meaningful tags if present
  const badges: string[] = [];
  if (profile?.copyability_tier) {
    badges.push(`Tier: ${profile.copyability_tier}`);
  }
  if (profile?.risk_bucket) {
    badges.push(`Risk: ${profile.risk_bucket}`);
  }

  const kpiItems = buildCreatorKpis(profile);
  const chartData = buildChartData(profile);
  const rows = Array.isArray(activity) ? activity : [];

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-4">
        <PageHeader
          title="Creator Intelligence"
          subtitle="Deep profile, execution quality, and trading activity for this creator."
        />

        {/* HEADER + KPIs */}
        <div className="space-y-3">
          {profileLoading && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              Loading creator profile…
            </div>
          )}

          {profileError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-red-500">
              Failed to load creator profile.
            </div>
          )}

          {profile && (
            <>
              <CreatorHeader alias={alias} pubkey={pubkey} badges={badges} />
              {kpiItems.length > 0 && (
                <CreatorKPIs items={kpiItems} cols={4} />
              )}
            </>
          )}
        </div>

        {/* CHARTS + SIDE PANEL */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
          <CreatorCharts data={chartData} />

          <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
            <div className="text-xs uppercase tracking-wide text-muted-foreground mb-1">
              Coming soon
            </div>
            <div>
              Risk scores, alerts, and copy wallet performance vs this creator
              will live here.
            </div>
          </div>
        </div>

        {/* ACTIVITY TABLE */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="text-muted-foreground">
              Activity ·{" "}
              {rows.length
                ? `${rows.length.toLocaleString()} trades`
                : "no trades yet"}
            </div>
          </div>

          {activityError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-red-500">
              Failed to load activity.
            </div>
          )}

          {activityLoading && !rows.length && !activityError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              Loading activity…
            </div>
          )}

          {!activityLoading && !rows.length && !activityError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              No activity recorded for this creator yet.
            </div>
          )}

          {rows.length > 0 && <CreatorActivityTable rows={rows} />}
        </div>
      </div>
    </DashboardShell>
  );
}

// ---- Helpers ----

function buildCreatorKpis(profile: any): { label: string; value: any }[] {
  if (!profile) return [];

  const out: { label: string; value: any }[] = [];

  if (profile.trades_7d != null) {
    out.push({
      label: "Trades 7d",
      value: Number(profile.trades_7d).toLocaleString(),
    });
  }

  if (profile.trades_30d != null) {
    out.push({
      label: "Trades 30d",
      value: Number(profile.trades_30d).toLocaleString(),
    });
  }

  if (profile.avg_execution_score_7d != null) {
    out.push({
      label: "Exec score 7d",
      value: Number(profile.avg_execution_score_7d).toFixed(1),
    });
  }

  if (profile.roi_me_7d != null) {
    out.push({
      label: "ROI me 7d",
      value: formatPct(profile.roi_me_7d),
    });
  }

  if (profile.followers_count != null) {
    out.push({
      label: "Followers",
      value: Number(profile.followers_count).toLocaleString(),
    });
  }

  return out;
}

function buildChartData(profile: any): { x: number; y: number }[] {
  const src = profile?.score_timeseries ?? profile?.exec_score_series;

  if (!Array.isArray(src) || !src.length) return [];

  return src.map((p: any, idx: number) => ({
    x: Number(p.x ?? p.ts ?? idx),
    y: Number(p.y ?? p.score ?? 0),
  }));
}

function formatPct(v: any): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  // assume backend sends pct (e.g. 12.3), not 0.123
  return `${n.toFixed(1)}%`;
}
