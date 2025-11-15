import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/providers/theme-provider";
import { QueryProvider } from "@/providers/query-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Sidebar } from "@/components/nav/sidebar";
import { Topbar } from "@/components/nav/topbar";

export const metadata: Metadata = {
  title: "Oculus",
  description: "Solana copy-trading analytics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <QueryProvider>
            <TooltipProvider delayDuration={200}>
              <div className="flex min-h-screen">
                <Sidebar />
                <div className="flex-1 flex flex-col">
                  <Topbar />
                  <main className="flex-1 overflow-y-auto p-4">{children}</main>
                </div>
              </div>
            </TooltipProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
