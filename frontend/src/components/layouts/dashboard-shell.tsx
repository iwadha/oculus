"use client";

import * as React from "react";
import { Sidebar } from "@/components/nav/sidebar";
import { Topbar } from "@/components/nav/topbar";

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh grid grid-cols-1 md:grid-cols-[240px_1fr]">
      {/* Sidebar (stacks above on mobile) */}
      <aside className="md:block border-r bg-background">
        <Sidebar />
      </aside>

      {/* Main area */}
      <div className="flex min-h-dvh flex-col">
        <Topbar />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
