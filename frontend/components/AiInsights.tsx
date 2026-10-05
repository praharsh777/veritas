"use client";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AnalysisReport, RiskLevel } from "@/lib/types";
import { ProvenanceBadge, Spinner } from "./ui";

const VIEW: Record<NonNullable<AnalysisReport["ai"]["assessment"]>, { label: string; cls: string }> = {
  likely_legitimate: { label: "AI leans legitimate", cls: "border-risk-low/40 bg-risk-low/10 text-risk-low" },
  unclear: { label: "AI is unsure", cls: "border-ink-500 bg-ink-700 text-mist-300" },
  suspicious: { label: "AI finds it suspicious", cls: "border-risk-mid/40 bg-risk-mid/10 text-risk-mid" },
  likely_scam: { label: "AI thinks it is likely a scam", cls: "border-risk-high/40 bg-risk-high/10 text-risk-high" },
};

// rank used only to tell the user when the AI's opinion and the rule-based verdict disagree
const AI_RANK = { likely_legitimate: 0, unclear: 1, suspicious: 2, likely_scam: 3 } as const;
const RULE_RANK: Record<RiskLevel, number> = { low_risk_signals: 0, needs_verification: 2, high_risk: 3 };

export default function AiInsights({ report, onReplace }: { report: AnalysisReport; onReplace: (r: AnalysisReport) => void }) {
  const ai = report.ai;
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function retry() {
    setBusy(true); setErr(null);
    try { onReplace(await api.retryAi(report.id)); }
    catch (e) { setErr(e instanceof ApiError ? e.message : "Retry failed."); }
    finally { setBusy(false); }
  }

  // Not configured at all
  if (!ai.configured) {
    return (
      <section className="card flex items-start gap-3 p-5">
        <ProvenanceBadge p="model_inference" />
        <div className="text-sm text-mist-300">
          <b className="text-mist-100">AI insights are off.</b> No AI provider is configured on the server, so this report uses rule-based checks only.
          Add a provider key in <code className="font-mono text-xs">backend/.env</code> to get an AI read of every message.
        </div>
      </section>
    );
  }

  // Configured but this attempt failed
  if (!ai.used) {
    return (
      <section className="card border-risk-mid/40 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1 text-sm">
            <div className="flex items-center gap-2"><ProvenanceBadge p="model_inference" /><b>AI insights unavailable for this run</b></div>
            <p className="mt-2 text-mist-300">The rule-based analysis below is complete. The AI step did not finish{ai.error ? <>: <span className="break-words font-mono text-xs text-mist-400">{ai.error}</span></> : "."}</p>
            <p className="mt-1 text-xs text-mist-500">Free models are often rate-limited. Retrying usually works, and listing several models in <code className="font-mono">OPENAI_COMPAT_MODEL</code> adds automatic fallback.</p>
            {err && <p className="mt-2 text-xs text-risk-high">{err}</p>}
          </div>
          {ai.can_retry && (
            <button className="btn-primary" onClick={retry} disabled={busy}>
              {busy ? <><Spinner /> Retrying…</> : "Retry AI insights"}
            </button>
          )}
        </div>
      </section>
    );
  }

  const v = VIEW[ai.assessment ?? "unclear"];
  const disagree = ai.assessment && Math.abs(AI_RANK[ai.assessment] - RULE_RANK[report.risk.risk_level]) >= 2;
  return (
    <section className="card p-5">
      <div className="flex flex-wrap items-center gap-2">
        <ProvenanceBadge p="model_inference" />
        <h3 className="text-base font-semibold">AI insights</h3>
        <span className={`chip ${v.cls}`}>{v.label}</span>
        <span className="ml-auto font-mono text-[11px] text-mist-500">{ai.provider}</span>
      </div>
      {ai.summary && <p className="mt-3 text-[15px] leading-relaxed">{ai.summary}</p>}

      {disagree && (
        <p className="mt-3 rounded-lg border border-risk-mid/40 bg-risk-mid/10 px-3 py-2 text-sm text-risk-mid">
          The AI’s read differs from the rule-based verdict. Neither is proof, so verify through an independent channel.
        </p>
      )}

      <div className="mt-4 grid gap-5 md:grid-cols-2">
        <div>
          <div className="label mb-2">What stands out</div>
          {ai.observations.length ? (
            <ul className="space-y-1.5 text-sm text-mist-300">
              {ai.observations.map((o, i) => <li key={i} className="flex gap-2"><span className="text-brand-400">•</span>{o}</li>)}
            </ul>
          ) : <p className="text-sm text-mist-500">No specific observations returned.</p>}
        </div>
        <div>
          <div className="label mb-2">Worth checking yourself</div>
          {ai.suggested_checks.length ? (
            <ul className="space-y-1.5 text-sm text-mist-300">
              {ai.suggested_checks.map((o, i) => <li key={i} className="flex gap-2"><span className="text-brand-400">→</span>{o}</li>)}
            </ul>
          ) : <p className="text-sm text-mist-500">No checks suggested.</p>}
        </div>
      </div>
      <p className="mt-4 text-[11px] leading-snug text-mist-500">
        AI output is validated and bounded: quotes must appear in the message, and it can add concern but cannot change the verdict level on its own.
      </p>
    </section>
  );
}
