"use client";
import { useState } from "react";
import type { ActionRecommendation } from "@/lib/types";

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      className="btn-ghost !px-2.5 !py-1 text-xs"
      onClick={async () => {
        try { await navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500); } catch { /* clipboard blocked */ }
      }}
    >{done ? "Copied" : "Copy"}</button>
  );
}

export default function VerifyPanel({ action }: { action: ActionRecommendation }) {
  return (
    <section aria-labelledby="vba" className="card relative overflow-hidden border-brand-500/40 p-6 shadow-[0_0_60px_-20px_rgb(var(--brand-500)/.5)]">
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-brand-500/10 blur-3xl" />
      <div className="label text-brand-400">Verify before you act</div>
      <h2 id="vba" className="mt-1 text-xl font-semibold leading-snug">{action.headline}</h2>

      {action.verification_steps.length > 0 && (
        <ol className="mt-5 space-y-3">
          {action.verification_steps.map((s) => (
            <li key={s.order} style={{ animationDelay: `${300 + s.order * 140}ms` }} className={`stagger flex gap-4 rounded-xl border p-4 transition-colors hover:border-brand-500/50 ${s.status === "unable_to_verify" ? "border-risk-mid/40 bg-risk-mid/5" : "border-ink-500 bg-ink-900/60"}`}>
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-500/20 text-sm font-bold text-brand-400">{s.order}</span>
              <div className="min-w-0 flex-1">
                <div className="font-medium">{s.title}</div>
                <p className="mt-0.5 text-sm text-mist-300">{s.detail}</p>
                {s.route && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs text-mist-400">Type this yourself:</span>
                    <code className="rounded-md bg-ink-950 px-2 py-1 font-mono text-sm text-brand-400">{s.route}</code>
                    <CopyButton text={s.route} />
                  </div>
                )}
                {s.status === "unable_to_verify" && <div className="mt-2 text-xs font-semibold text-risk-mid">Unable to independently verify</div>}
              </div>
            </li>
          ))}
        </ol>
      )}

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <div className="label mb-2 text-risk-low">Do now</div>
          <ul className="space-y-1.5 text-sm text-mist-100">
            {action.do_now.map((t, i) => <li key={i} className="flex gap-2"><span className="text-risk-low">✓</span>{t}</li>)}
          </ul>
        </div>
        <div>
          <div className="label mb-2 text-risk-high">Do not</div>
          <ul className="space-y-1.5 text-sm text-mist-100">
            {action.do_not.map((t, i) => <li key={i} className="flex gap-2"><span className="text-risk-high">✕</span>{t}</li>)}
          </ul>
        </div>
      </div>

      {action.report_to.length > 0 && (
        <div className="mt-5 border-t border-ink-600 pt-4 text-xs text-mist-400">
          <span className="label mr-2">If you were targeted, report to</span>{action.report_to.join(" · ")}
        </div>
      )}
    </section>
  );
}
