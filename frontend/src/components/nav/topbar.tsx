"use client";

import * as React from "react";
import Link from "next/link";
import { useTheme } from "next-themes";

export function Topbar() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="mx-auto flex h-12 items-center gap-3 px-3">
        <Link href="/" className="text-sm font-medium hover:underline">
          Dashboard
        </Link>
        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // ensure consistent hook order and safe hydration
  React.useEffect(() => setMounted(true), []);

  const toggleTheme = React.useCallback(() => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  }, [resolvedTheme, setTheme]);

  if (!mounted) {
    // render placeholder before hydration completes
    return <button className="px-2 py-1 text-xs rounded-md border opacity-50">—</button>;
  }

  return (
    <button
      className="px-2 py-1 text-xs rounded-md border"
      onClick={toggleTheme}
      title="Toggle theme"
    >
      {resolvedTheme === "dark" ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
}
