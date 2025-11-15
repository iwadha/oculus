"use client";

export function CreatorBadges({ items = [] as string[] }) {
  if (!items?.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((b, i) => (
        <span key={i} className="px-2 py-0.5 rounded bg-muted text-xs">
          {b}
        </span>
      ))}
    </div>
  );
}
