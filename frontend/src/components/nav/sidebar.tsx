"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/", label: "Dashboard" }, 
  { href: "/trades", label: "Live Intelligence" },
  { href: "/creators", label: "Creator Directory" },
  { href: "/wallets", label: "Wallet Ops" },
  { href: "/ladder", label: "Ladder Analysis" },
  { href: "/alerts", label: "Alerts Inbox" },
  { href: "/rules", label: "Automation Rules" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="p-3">
      <div className="px-3 py-2">
        <div className="text-sm font-semibold tracking-wide">OCULUS</div>
        <div className="text-xs text-muted-foreground">Solana Copy-Trading</div>
      </div>
      <nav className="mt-2 grid gap-1">
        {ITEMS.map((it) => {
          const active = pathname?.startsWith(it.href);
          return (
            <Link
              key={it.href}
              href={it.href}
              className={`px-3 py-2 rounded-md text-sm hover:bg-muted ${
                active ? "bg-muted font-medium" : ""
              }`}
            >
              {it.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-4 border-t pt-3 px-3 text-xs text-muted-foreground">
        <div>v0.1 · Light/Dark ready</div>
      </div>
    </div>
  );
}
