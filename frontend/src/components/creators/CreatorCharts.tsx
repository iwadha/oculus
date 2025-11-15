"use client";

import * as React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

/**
 * Renders a small execution-score trend. `data` is array of { x, y }.
 * Uses Recharts (already installed).
 */
export function CreatorCharts({
  data,
  height = 220,
}: {
  data: { x: number; y: number }[];
  height?: number;
}) {
  if (!data?.length) {
    return (
      <div className="border rounded-2xl p-6 text-sm text-muted-foreground">
        No chart data.
      </div>
    );
  }

  const chartData = data.map((d) => ({ x: d.x, y: Number(d.y ?? 0) }));

  return (
    <div className="border rounded-2xl p-3">
      <div className="h-[220px] md:h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
            <XAxis
              dataKey="x"
              hide
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={["auto", "auto"]}
              hide
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => [String(value), "Score"]}
              labelFormatter={() => ""}
              cursor={{ strokeDasharray: "3 3" }}
            />
            <Line
              type="monotone"
              dataKey="y"
              stroke="currentColor"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
