"use client";

export function CreatorKPIs({
  items,
  cols = 4,
}: {
  items: { label: string; value: any }[];
  cols?: 2 | 3 | 4 | 5 | 6;
}) {
  const grid = `grid grid-cols-2 md:grid-cols-${cols} gap-3`;
  return (
    <div className={grid}>
      {items.map((it, i) => (
        <div key={i} className="border rounded-2xl p-4">
          <div className="text-xs text-muted-foreground">{it.label}</div>
          <div className="text-lg font-semibold mt-1">
            {it.value ?? "—"}
          </div>
        </div>
      ))}
    </div>
  );
}
