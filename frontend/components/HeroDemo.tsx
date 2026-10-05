"use client";
import { useEffect, useState } from "react";
import { prefersReducedMotion } from "@/lib/hooks";

// Fictional sample. Phases: 0 idle → 1 highlight phrases → 2 signals → 3 verdict → 4 safe next step → loop
const PHASES = 5;

function Mark({ on, children }: { on: boolean; children: React.ReactNode }) {
  return (
    <span className={`rounded px-0.5 transition-all duration-500 ${on ? "bg-risk-high/20 text-risk-high shadow-[inset_0_-2px_0_rgb(var(--risk-high)/.7)]" : ""}`}>
      {children}
    </span>
  );
}

export default function HeroDemo() {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    if (prefersReducedMotion()) { setPhase(4); return; }
    const hold = [900, 1300, 1500, 1500, 3200];
    let t: ReturnType<typeof setTimeout>;
    const step = (p: number) => {
      setPhase(p);
      t = setTimeout(() => step((p + 1) % PHASES), hold[p]);
    };
    step(0);
    return () => clearTimeout(t);
  }, []);

  const signals = [
    ["Urgency / time pressure", "Observed in message", "prov-obs"],
    ["Asks for a one-time code", "Rule-based check", "prov-rule"],
    ["Link imitates Chase", "Rule-based check", "prov-rule"],
  ] as const;

  return (
    <div className="card relative overflow-hidden p-5" aria-label="Example analysis" role="img">
      {/* scanning line while "analysing" */}
      {phase === 1 && <div className="pointer-events-none absolute inset-x-0 top-0 h-1/4 animate-scan bg-gradient-to-b from-transparent via-brand-500/15 to-transparent" />}

      <div className="mb-3 flex items-center justify-between">
        <span className="label">Sample message · SMS</span>
        <span className="chip border-ink-500 text-mist-400">fictional</span>
      </div>

      <div className="rounded-2xl rounded-bl-md bg-ink-700 p-4 text-sm leading-relaxed text-mist-100">
        Chase Alert: Unusual sign-in detected. Your account will be{" "}
        <Mark on={phase >= 1}>suspended in 30 minutes</Mark>.{" "}
        <Mark on={phase >= 1}>Verify now</Mark>:{" "}
        <Mark on={phase >= 1}>chase-secure-verify.top/login</Mark>. Reply with the{" "}
        <Mark on={phase >= 1}>6-digit code</Mark> we send you.
      </div>

      <div className="mt-4 min-h-[7.25rem] space-y-2">
        {signals.map(([label, prov, cls], i) => (
          <div key={label}
            className={`flex items-center justify-between gap-2 rounded-lg border border-ink-600 bg-ink-900/60 px-3 py-2 text-sm transition-all duration-500 ${phase >= 2 ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}
            style={{ transitionDelay: phase >= 2 ? `${i * 160}ms` : "0ms" }}>
            <span>{label}</span>
            <span className={`chip ${cls}`}>{prov}</span>
          </div>
        ))}
      </div>

      <div className={`mt-3 flex items-center justify-between rounded-xl border border-risk-high/40 bg-risk-high/10 px-4 py-3 transition-all duration-500 ${phase >= 3 ? "scale-100 opacity-100" : "scale-95 opacity-0"}`}>
        <div className="flex items-center gap-2 font-semibold text-risk-high">
          <span className="h-2 w-2 animate-pulseRing rounded-full bg-risk-high" /> High Risk
        </div>
        <div className="text-xs text-mist-300">Risk <b className="font-mono text-mist-100">85</b> · Confidence <b className="font-mono text-mist-100">95</b></div>
      </div>

      <div className={`mt-3 rounded-xl border border-brand-500/40 bg-brand-500/10 px-4 py-3 text-sm transition-all duration-500 ${phase >= 4 ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}>
        <div className="label text-brand-400">Verify before you act</div>
        <div className="mt-1">Don’t use the link. Open your bank’s app, or type <code className="rounded bg-ink-950 px-1.5 py-0.5 font-mono text-brand-400">chase.com</code> yourself.</div>
      </div>
    </div>
  );
}
