"use client";

export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-destructive">
      {message ?? "Something went wrong."}
    </div>
  );
}
