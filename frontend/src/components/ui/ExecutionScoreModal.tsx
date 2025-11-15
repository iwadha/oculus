"use client";

import * as React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";


import { ExecutionScoreSparkline } from "./ExecutionScoreSparkline";

export type ExecutionScoreModalProps = {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  score: number | null;
  recent?: number[]; // optional history to render sparkline
  meta?: Record<string, any>;
};

export function ExecutionScoreModal({
  open,
  onOpenChange,
  score,
  recent = [],
  meta = {},
}: ExecutionScoreModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Execution Quality</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="text-sm">
            <span className="text-muted-foreground">Score:</span>{" "}
            <span className="font-medium">{score ?? "n/a"}</span>
          </div>

          {!!recent.length && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">
                Recent scores
              </div>
              <ExecutionScoreSparkline values={recent} height={60} />
            </div>
          )}

          {Object.keys(meta).length > 0 && (
            <div>
              <div className="text-xs text-muted-foreground mb-1">Details</div>
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(meta).map(([k, v]) => (
                    <tr key={k}>
                      <td className="py-1 text-muted-foreground pr-4">{k}</td>
                      <td className="py-1 font-mono">{String(v)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
