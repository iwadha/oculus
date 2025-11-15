// frontend/src/app/(dashboard)/page.tsx
"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["kpis"],
    queryFn: () => api.getKpis(),
    refetchInterval: 15_000,
  });

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Oculus Dashboard</h1>


      {/* KPIs */}
      <section className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
        <Kpi label="Active creators" value={fmtInt(data?.active_creators)} />
        <Kpi
          label="Buy %"
          value={data?.buy_pct != null ? `${data.buy_pct.toFixed(1)}%` : "—"}
        />
        <Kpi label="Avg blocks" value={fmtNum(data?.avg_blocks)} />
        <Kpi label="Avg exec score" value={fmtNum(data?.avg_score)} />
        <Kpi label="TPS" value={fmtNum(data?.tps)} />
      </section>

      {/* Loading / Error */}
      {isLoading && <div>Loading…</div>}
      {error && (
        <div className="text-destructive mb-3">
          Failed to load KPIs.{" "}
          <button className="underline" onClick={() => refetch()}>
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

/* ---------- helpers ---------- */

function Kpi({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="border rounded-2xl p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold mt-1">{value ?? "—"}</div>
    </div>
  );
}

function fmtNum(n?: number | null, dp = 2) {
  return n == null ? "—" : n.toFixed(dp);
}
function fmtInt(n?: number | null) {
  return n == null ? "—" : new Intl.NumberFormat().format(Math.round(n));
}
