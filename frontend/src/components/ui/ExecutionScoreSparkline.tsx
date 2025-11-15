"use client";

import * as React from "react";

/**
 * Minimal inline SVG sparkline.
 * values: Array of 0..100 (or any numeric scale). We auto-scale to the chart.
 */
export function ExecutionScoreSparkline({
  values,
  width = 300,
  height = 48,
  strokeWidth = 2,
}: {
  values: number[];
  width?: number;
  height?: number;
  strokeWidth?: number;
}) {
  if (!values?.length) return null;

  const xs = values.map((_, i) => i);
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const minX = 0;
  const maxX = xs[xs.length - 1] || 1;

  const px = (x: number) =>
    (x - minX) / (maxX - minX || 1) * (width - 8) + 4;
  const py = (y: number) =>
    height - ((y - minV) / (maxV - minV || 1)) * (height - 8) - 4;

  const d = values
    .map((y, i) => `${i === 0 ? "M" : "L"} ${px(i)} ${py(y)}`)
    .join(" ");

  return (
    <svg width={width} height={height} className="block">
      <path d={d} stroke="currentColor" fill="none" strokeWidth={strokeWidth} />
    </svg>
  );
}
