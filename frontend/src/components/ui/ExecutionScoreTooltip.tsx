"use client";

import * as React from "react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function ExecutionScoreTooltip({
  score,
  children,
}: {
  score: number;
  children: React.ReactNode;
}) {
  const label =
    score >= 80
      ? "Excellent execution"
      : score >= 60
      ? "Good execution"
      : score >= 40
      ? "Average execution"
      : "Poor execution";

  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent side="top">
        <div className="text-xs">
          <div className="font-medium">Execution Score: {score}</div>
          <div className="text-muted-foreground">{label}</div>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
