"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export function Nav(){
const pathname = usePathname();
const items = [
{ href: "/", label: "Dashboard" },
{ href: "/trades", label: "Live" },
{ href: "/creators", label: "Creators" },
{ href: "/wallets", label: "Wallets" },
{ href: "/alerts", label: "Inbox" },
{ href: "/rules", label: "Rules" },
];
return (
<nav className="flex gap-2">
{items.map(it => (
<Link key={it.href} href={it.href} className={`px-3 py-1.5 rounded ${pathname===it.href?"bg-muted font-medium":"text-muted-foreground hover:bg-muted"}`}>{it.label}</Link>
))}
</nav>
);
}