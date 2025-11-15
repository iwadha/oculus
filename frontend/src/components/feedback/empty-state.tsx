"use client";

export function EmptyState({ children }: { children?: React.ReactNode }) {
  return (
    <div className="border border-dashed rounded-2xl p-8 text-center text-muted-foreground">
      {children ?? "Nothing to show yet."}
    </div>
  );
}
