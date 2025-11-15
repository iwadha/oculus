"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import DashboardShell from "@/components/layouts/dashboard-shell";
import { PageHeader } from "@/components/layouts/page-header";
import { api, type RuleRow } from "@/lib/api";

export default function RulesPage() {
  const { data, isLoading, isError, refetch } = useQuery<RuleRow[]>({
    queryKey: ["rules"],
    queryFn: () => api.getRules(),
    refetchInterval: 60000,
  });

  const rules = data ?? [];
  const enabledCount = rules.filter((r) => r.enabled).length;

  return (
    <DashboardShell>
      <div className="px-4 py-3 space-y-4">
        <PageHeader
          title="Automation Rules"
          subtitle="Conditions that trigger alerts and actions across wallets and creators."
        />

        {/* Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <RuleMetric label="Total rules" value={rules.length} />
          <RuleMetric label="Enabled" value={enabledCount} />
          <RuleMetric label="Disabled" value={rules.length - enabledCount} />
          <RuleMetric label="Scope" value="Wallet / Creator / Fleet" />
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between text-xs">
          <div className="text-muted-foreground">
            Rules are currently read-only in this UI. Changes are managed in
            backend config / admin flows.
          </div>
          <button
            type="button"
            onClick={() => refetch()}
            className="inline-flex items-center rounded-md border px-2 py-1 text-[11px] font-medium bg-background hover:bg-accent"
          >
            Refresh
          </button>
        </div>

        {/* Rules list */}
        <div className="space-y-2">
          {isError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-red-500">
              Failed to load rules.
            </div>
          )}

          {isLoading && !rules.length && !isError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              Loading rules…
            </div>
          )}

          {!isLoading && !rules.length && !isError && (
            <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
              No rules defined yet. Once rules are created in the backend, they will
              appear here.
            </div>
          )}

          {rules.map((rule) => (
            <RuleCard key={rule.id} rule={rule} />
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}

function RuleMetric({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl border bg-card px-3 py-2 flex flex-col justify-between">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
    </div>
  );
}

function RuleCard({ rule }: { rule: RuleRow }) {
  const enabled = !!rule.enabled;
  const severity = (rule.severity || "").toUpperCase();

  const sevTone =
    severity === "CRITICAL"
      ? "bg-red-500/10 text-red-400"
      : severity === "HIGH"
      ? "bg-amber-500/10 text-amber-300"
      : "bg-zinc-700 text-zinc-200";

  return (
    <div className="rounded-2xl border bg-card px-4 py-3 flex flex-col gap-2 text-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-col">
          <div className="text-sm font-semibold">{rule.name}</div>
          {rule.scope && (
            <div className="text-[11px] text-muted-foreground">
              Scope: {rule.scope}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {rule.severity && (
            <span
              className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium ${sevTone}`}
            >
              {severity}
            </span>
          )}
          <span
            className={
              "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium " +
              (enabled
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-zinc-700 text-zinc-200")
            }
          >
            {enabled ? "Enabled" : "Disabled"}
          </span>
        </div>
      </div>
      {rule.description && (
        <div className="text-xs text-muted-foreground">
          {rule.description}
        </div>
      )}
      {rule.created_at && (
        <div className="text-[11px] text-muted-foreground">
          Created: {new Date(rule.created_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}
