"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";
import ThemeToggle from "./ThemeToggle";

const links = [
  { href: "/analyze", label: "Analyze" },
  { href: "/scenarios", label: "Scenarios" },
  { href: "/history", label: "History" },
];

export default function Nav() {
  const path = usePathname();
  const [health, setHealth] = useState<Health | null | "down">(null);
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth("down")); }, []);

  return (
    <header className="sticky top-0 z-30 border-b border-ink-600/60 bg-ink-950/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-5 py-3">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-500/15 ring-1 ring-brand-500/40 transition duration-300 group-hover:rotate-[-6deg] group-hover:scale-105">
            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--brand-400))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6l8-3z" /><path d="M8.5 12.2l2.4 2.4 4.6-4.8" /></svg>
          </span>
          <span className="text-lg font-bold tracking-[0.18em]">VERITAS</span>
        </Link>

        <nav className="flex items-center gap-1 rounded-xl border border-ink-600/60 bg-ink-800/60 p-1" aria-label="Main">
          {links.map((l) => {
            const active = path?.startsWith(l.href);
            return (
              <Link key={l.href} href={l.href} aria-current={active ? "page" : undefined}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-200 ${active ? "bg-brand-500/15 text-brand-400 shadow-sm" : "text-mist-300 hover:bg-ink-700 hover:text-mist-100"}`}>
                {l.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 text-xs text-mist-400 md:flex" aria-live="polite">
            {health === null ? <span className="skeleton h-3 w-28" /> : health === "down" ? (
              <><span className="h-2 w-2 rounded-full bg-risk-high" /> Backend offline</>
            ) : (
              <><span className="relative flex h-2 w-2"><span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-60 ${health.ai_enabled ? "bg-risk-low" : "bg-risk-mid"}`} /><span className={`relative inline-flex h-2 w-2 rounded-full ${health.ai_enabled ? "bg-risk-low" : "bg-risk-mid"}`} /></span>
                {health.ai_enabled ? `AI: ${health.ai_provider}` : "AI layer off · rule engine active"}</>
            )}
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
