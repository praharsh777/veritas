"use client";
import { useEffect, useState } from "react";
import type { TimelineStep } from "@/lib/types";
import { Spinner } from "./ui";

const PLAN = [
  "Normalize & sanitize input",
  "Extract entities, claims & requests",
  "Social-engineering signals",
  "URL, domain & sender checks",
  "AI reasoning",
  "Cross-check against reference data",
  "Risk & confidence model",
];

/** Live progress shown while the request is running. Actual per-step results replace it when the report arrives. */
export function LiveTimeline({ running }: { running: boolean }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (!running) { setI(0); return; }
    const t = setInterval(() => setI((x) => Math.min(x + 1, PLAN.length - 1)), 380);
    return () => clearInterval(t);
  }, [running]);
  const pct = running ? ((i + 1) / PLAN.length) * 100 : 0;
  return (
    <div>
      <div className="mb-4 h-1 w-full overflow-hidden rounded-full bg-ink-600" aria-hidden>
        <div className="h-full rounded-full bg-brand-500 transition-[width] duration-500 ease-out" style={{ width: `${pct}%` }} />
      </div>
      <ol className="space-y-2">
        {PLAN.map((label, idx) => {
          const state = !running ? "idle" : idx < i ? "done" : idx === i ? "run" : "wait";
          return (
            <li key={label} className={`flex items-center gap-3 text-sm transition-colors duration-300 ${state === "wait" || state === "idle" ? "text-mist-500" : "text-mist-100"}`}>
              <span className="grid h-5 w-5 place-items-center">
                {state === "run" ? <Spinner className="text-brand-400" /> : state === "done" ? <span className="animate-pop text-brand-400">✓</span> : <span className="h-1.5 w-1.5 rounded-full bg-ink-500" />}
              </span>
              {label}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

const ICON: Record<TimelineStep["status"], { sym: string; cls: string }> = {
  done: { sym: "✓", cls: "text-brand-400" },
  skipped: { sym: "–", cls: "text-mist-500" },
  failed: { sym: "!", cls: "text-risk-high" },
};

export function ResultTimeline({ steps }: { steps: TimelineStep[] }) {
  return (
    <ol className="space-y-2.5">
      {steps.map((s, i) => (
        <li key={s.id} className="stagger flex gap-3 text-sm" style={{ animationDelay: `${i * 60}ms` }}>
          <span className={`mt-0.5 w-4 text-center font-bold ${ICON[s.status].cls}`}>{ICON[s.status].sym}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-2">
              <span className={s.status === "skipped" ? "text-mist-400" : "text-mist-100"}>{s.label}</span>
              {s.duration_ms > 0 && <span className="font-mono text-xs text-mist-500">{s.duration_ms} ms</span>}
            </div>
            {s.detail && <div className="text-xs text-mist-400">{s.detail}</div>}
          </div>
        </li>
      ))}
    </ol>
  );
}
