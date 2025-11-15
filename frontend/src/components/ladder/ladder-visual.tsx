"use client";

import * as React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";

/**
 * LadderVisual
 * Renders crowding around an event slot.
 * Expects an array like: [{ relative: -3, copies: 12, sources: 3 }, ...]
 *   - relative < 0  => copies ahead of the source trade (earlier slots)
 *   - relative = 0  => copies in the same slot
 *   - relative > 0  => copies behind (later slots)
 */
export function LadderVisual({
  data,
  height = 260,
  showSources = true,
}: {
  data: { relative: number; copies: number; sources?: number }[];
  height?: number;
  showSources?: boolean;
}) {
  const rows = React.useMemo(() => {
    if (!Array.isArray(data) || !data.length) return [];
    // Ensure stable sort by relative slot
    const sorted = [...data].sort((a, b) => a.relative - b.relative);
    return sorted.map((d) => ({
      x: d.relative,         // bucket label (relative slots)
      copies: Number(d.copies ?? 0),
      sources: Number(d.sources ?? 0),
      side: d.relative === 0 ? "at" : d.relative < 0 ? "ahead" : "behind",
    }));
  }, [data]);

  if (!rows.length) {
    return (
      <div className="border rounded-2xl p-6 text-sm text-muted-foreground">
        No ladder data.
      </div>
    );
  }

  // Colors (inherited from currentColor for accessibility, but we set fills for clarity)
  const colorAhead = "rgb(52 211 153)";   // emerald-400
  const colorAt    = "rgb(163 163 163)";  // zinc-400
  const colorBehind= "rgb(244 63 94)";    // rose-500

  return (
    <div className="border rounded-2xl p-3">
      <div className="flex items-center justify-between px-1 pb-2">
        <div className="text-sm text-muted-foreground">
          Copies per slot (negative = ahead, 0 = at event, positive = behind)
        </div>
        <Legend
          items={[
            { label: "Ahead", color: colorAhead },
            { label: "At", color: colorAt },
            { label: "Behind", color: colorBehind },
          ]}
        />
      </div>

      <div className="h-[260px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rows}
            margin={{ left: 8, right: 8, top: 8, bottom: 8 }}
            barCategoryGap={2}
          >
            <XAxis
              dataKey="x"
              tick={{ fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              label={{ value: "Relative slots", position: "insideBottom", offset: -6, fontSize: 12 }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              formatter={(value: any, name: string) => {
                if (name === "copies") return [String(value), "Copies"];
                if (name === "sources") return [String(value), "Sources"];
                return [String(value), name];
              }}
              labelFormatter={(label: any) => `Slot ${label}`}
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
            />

            {/* vertical zero line */}
            <ReferenceLine x={0} stroke="currentColor" strokeOpacity={0.4} />

            {/* Main bars: copies */}
            <Bar dataKey="copies" name="copies" radius={[4, 4, 0, 0]}>
              {rows.map((r, i) => (
                <Cell
                  key={`c-${i}`}
                  fill={r.side === "ahead" ? colorAhead : r.side === "at" ? colorAt : colorBehind}
                />
              ))}
            </Bar>

            {/* Optional overlay for sources (thin bar) */}
            {showSources && (
              <Bar
                dataKey="sources"
                name="sources"
                radius={[4, 4, 0, 0]}
                barSize={6}
                fill="rgb(59 130 246)"   // blue-500
              />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <div className="flex items-center gap-3 text-xs">
      {items.map((it) => (
        <div key={it.label} className="flex items-center gap-1">
          <span
            className="inline-block h-2 w-2 rounded-[2px]"
            style={{ backgroundColor: it.color }}
          />
          <span className="text-muted-foreground">{it.label}</span>
        </div>
      ))}
    </div>
  );
}
