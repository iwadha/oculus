"use client";

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="grid gap-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-9 w-full rounded-md bg-muted animate-pulse" />
      ))}
    </div>
  );
}
