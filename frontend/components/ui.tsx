"use client";
import { useEffect, useState } from "react";
import type { Provenance, RiskLevel } from "@/lib/types";
import { useMounted } from "@/lib/hooks";
import { PROVENANCE } from "@/lib/provenance";

export { PROVENANCE };

export function ProvenanceBadge({ p }: { p: Provenance }) {
  const m = PROVENANCE[p];
  return <span title={m.help} className={`chip ${m.cls}`}>{m.label}</span>;
}

export function ProvenanceLegend() {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-mist-400">
      <span>Every finding is labelled by where it comes from:</span>
      {(Object.keys(PROVENANCE) as Provenance[]).map((p) => <ProvenanceBadge key={p} p={p} />)}
    </div>
  );
}

export const LEVEL_STYLE: Record<RiskLevel, { text: string; ring: string; bg: string; bar: string; dot: string; glow: string }> = {
  high_risk: { text: "text-risk-high", ring: "border-risk-high/50", bg: "bg-risk-high/10", bar: "bg-risk-high", dot: "bg-risk-high", glow: "shadow-[0_0_60px_-24px_rgb(var(--risk-high)/.6)]" },
  needs_verification: { text: "text-risk-mid", ring: "border-risk-mid/50", bg: "bg-risk-mid/10", bar: "bg-risk-mid", dot: "bg-risk-mid", glow: "shadow-[0_0_60px_-24px_rgb(var(--risk-mid)/.5)]" },
  low_risk_signals: { text: "text-risk-low", ring: "border-risk-low/50", bg: "bg-risk-low/10", bar: "bg-risk-low", dot: "bg-risk-low", glow: "shadow-[0_0_60px_-24px_rgb(var(--risk-low)/.5)]" },
};

export function LevelPill({ level, label }: { level: RiskLevel; label: string }) {
  const s = LEVEL_STYLE[level];
  return (
    <span className={`inline-flex animate-pop items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold ${s.ring} ${s.bg} ${s.text}`}>
      <span className={`relative h-2 w-2 rounded-full ${s.dot} ${level === "high_risk" ? "animate-pulseRing" : ""}`} />{label}
    </span>
  );
}

/** Meter that animates from 0 to its value on mount. */
export function Meter({ value, className = "bg-brand-500", label }: { value: number; className?: string; label: string }) {
  const mounted = useMounted(120);
  return (
    <div role="meter" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} className="h-2 w-full overflow-hidden rounded-full bg-ink-600">
      <div className={`h-full rounded-full transition-[width] duration-1000 ease-out ${className}`} style={{ width: mounted ? `${value}%` : "0%" }} />
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return <span aria-hidden className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent ${className}`} />;
}

export function ErrorBanner({ message, onClose }: { message: string; onClose?: () => void }) {
  return (
    <div role="alert" className="flex animate-fadeUp items-start justify-between gap-3 rounded-xl border border-risk-high/40 bg-risk-high/10 px-4 py-3 text-sm text-risk-high">
      <span>{message}</span>
      {onClose && <button onClick={onClose} className="opacity-70 transition hover:opacity-100" aria-label="Dismiss">✕</button>}
    </div>
  );
}

export function Empty({ title, body, children }: { title: string; body: string; children?: React.ReactNode }) {
  return (
    <div className="card flex animate-fadeUp flex-col items-center gap-2 p-10 text-center">
      <div className="mb-1 grid h-12 w-12 place-items-center rounded-2xl bg-brand-500/10 text-brand-400">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6l8-3z" /></svg>
      </div>
      <div className="text-lg font-semibold">{title}</div>
      <p className="max-w-md text-sm text-mist-400">{body}</p>
      {children}
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden />;
}

/** Placeholder shown in the report area while an analysis runs. */
export function ReportSkeleton() {
  return (
    <div className="space-y-5" aria-busy="true" aria-label="Analysis in progress">
      <div className="card space-y-4 p-6">
        <div className="flex gap-3"><Skeleton className="h-7 w-36" /><Skeleton className="h-7 w-44" /></div>
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-2 w-full" />
      </div>
      <div className="grid gap-5 lg:grid-cols-5">
        <div className="card space-y-3 p-5 lg:col-span-3">
          <Skeleton className="h-5 w-40" />
          {[0, 1, 2].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
        </div>
        <div className="card space-y-3 p-6 lg:col-span-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    </div>
  );
}

export function timeAgo(iso: string) {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

/** Tiny hook-free helper kept for symmetry with other components. */
export function useIsClient() {
  const [c, setC] = useState(false);
  useEffect(() => setC(true), []);
  return c;
}
