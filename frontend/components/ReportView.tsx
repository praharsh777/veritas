"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import type { AnalysisReport } from "@/lib/types";
import EvidenceDrawer from "./EvidenceDrawer";
import RiskRing from "./RiskRing";
import { ResultTimeline } from "./Timeline";
import AiInsights from "./AiInsights";
import VerifyPanel from "./VerifyPanel";
import { LEVEL_STYLE, LevelPill, Meter, ProvenanceBadge, ProvenanceLegend } from "./ui";
import { useCountUp } from "@/lib/hooks";

/** Staggered entrance: each block fades up slightly after the previous one. */
function Rv({ i, children, className = "" }: { i: number; children: React.ReactNode; className?: string }) {
  return <div className={`stagger ${className}`} style={{ animationDelay: `${i * 90}ms` }}>{children}</div>;
}

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="card p-5">
      <div className="mb-3">
        <h3 className="text-base font-semibold">{title}</h3>
        {hint && <p className="text-xs text-mist-400">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

function Expandable({ head, children }: { head: React.ReactNode; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <li className={`rounded-xl border bg-ink-900/50 transition-colors duration-200 ${open ? "border-brand-500/40" : "border-ink-600"}`}>
      <button className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="min-w-0 flex-1">{head}</span>
        <svg className={`shrink-0 text-mist-400 transition-transform duration-300 ${open ? "rotate-180" : ""}`} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M6 9l6 6 6-6" /></svg>
      </button>
      {/* grid-rows trick gives a smooth height animation without measuring */}
      <div className={`grid transition-all duration-300 ease-out ${open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
        <div className="overflow-hidden">
          <div className="space-y-2 border-t border-ink-600 px-4 py-3 text-sm text-mist-300">{children}</div>
        </div>
      </div>
    </li>
  );
}

const CLAIM_STYLE = {
  consistent_with_reference: { t: "Matches reference", c: "text-risk-low" },
  inconsistent_with_reference: { t: "Does not match reference", c: "text-risk-high" },
  unable_to_verify: { t: "Unable to independently verify", c: "text-risk-mid" },
} as const;

export default function ReportView({ report: initial }: { report: AnalysisReport }) {
  const [report, setReport] = useState(initial);
  const [drawer, setDrawer] = useState(false);
  const [fb, setFb] = useState<string | null>(report.feedback);
  const [fbErr, setFbErr] = useState(false);
  const r = report.risk;
  const s = LEVEL_STYLE[r.risk_level];
  const conf = useCountUp(r.confidence_score, 1100, 250);
  const lowConfHigh = r.risk_level === "high_risk" && r.confidence_score < 55;
  const ex = report.extraction;

  async function sendFeedback(o: "was_scam" | "was_legitimate" | "not_sure") {
    try { await api.feedback(report.id, o); setFb(o); setFbErr(false); } catch { setFbErr(true); }
  }

  return (
    <div className="space-y-5">
      {/* 1. Verdict */}
      <Rv i={0}>
        <section className={`card border ${s.ring} ${s.glow} p-6`}>
          <div className="flex flex-wrap items-center gap-6">
            <RiskRing value={r.risk_score} tone={s.text} label="Risk" />
            <div className="min-w-0 flex-1 basis-72">
              <div className="flex flex-wrap items-center gap-2">
                <LevelPill level={r.risk_level} label={r.verdict_label} />
                <span className="chip border-ink-500 text-mist-300">{report.category_label}</span>
                <span className="chip border-ink-500 text-mist-400">{report.input.kind === "image" ? "Screenshot" : report.input.kind === "url" ? "Link" : report.input.kind === "document" ? "Document" : "Message"}</span>
              </div>
              <p className="mt-3 text-lg leading-snug">{report.summary}</p>
              {lowConfHigh && <p className="mt-2 rounded-lg border border-risk-mid/40 bg-risk-mid/10 px-3 py-2 text-sm text-risk-mid">High concern, but verification is incomplete.</p>}
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn-ghost" onClick={() => setDrawer(true)}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg>
                  Open evidence ({report.evidence.length})
                </button>
              </div>
            </div>
            <div className="w-full sm:w-64">
              <div className="mb-1 flex items-baseline justify-between"><span className="label">Confidence</span><span className="font-mono text-2xl font-bold text-brand-400">{conf}<span className="text-sm text-mist-500">/100</span></span></div>
              <Meter value={r.confidence_score} label="Confidence score" />
              <p className="mt-3 text-[11px] leading-snug text-mist-500">{r.score_disclaimer} Confidence reflects how much independent evidence supports this assessment.</p>
            </div>
          </div>
        </section>
      </Rv>

      <Rv i={1}><AiInsights report={report} onReplace={setReport} /></Rv>

      <div className="grid gap-5 lg:grid-cols-5">
        {/* 2. Why */}
        <div className="space-y-5 lg:col-span-3">
          <Rv i={1}>
            <Section title="Why we think this" hint="Expand any reason to see the exact text or rule behind it.">
              <div className="mb-3"><ProvenanceLegend /></div>
              {report.threat_signals.length + report.technical_signals.length === 0 ? (
                <p className="text-sm text-mist-300">No common scam indicators were found. That is not proof the message is genuine. Verify anything involving money or personal data.</p>
              ) : (
                <ul className="space-y-2">
                  {report.threat_signals.map((t) => (
                    <Expandable key={t.id} head={
                      <span className="flex flex-wrap items-center gap-2"><span className="font-medium">{t.label}</span><ProvenanceBadge p={t.provenance} /></span>}>
                      <p>{t.explanation}</p>
                      {t.excerpts.map((x, i) => <blockquote key={i} className="border-l-2 border-brand-500/60 pl-3 font-mono text-xs text-mist-100">“{x}”</blockquote>)}
                    </Expandable>
                  ))}
                  {report.technical_signals.map((t, i) => (
                    <Expandable key={t.id + i} head={
                      <span className="flex flex-wrap items-center gap-2"><span className="font-medium">{t.label}</span><ProvenanceBadge p={t.provenance} /></span>}>
                      <p>{t.detail}</p>
                      <code className="block break-all rounded bg-ink-950 px-2 py-1 font-mono text-xs text-mist-300">{t.subject}</code>
                    </Expandable>
                  ))}
                </ul>
              )}
            </Section>
          </Rv>

          <Rv i={2}>
            <Section title="What the message asks of you" hint="Extracted from the text; nothing here has been executed or visited.">
              <div className="grid gap-4 text-sm sm:grid-cols-2">
                <Block title="Requested actions" items={ex.requested_actions.map((a) => a.label)} />
                <Block title="Requested sensitive data" items={ex.requested_data.map((a) => a.label)} danger />
                <Block title="Deadlines" items={ex.deadlines} />
                <Block title="Payment requests" items={ex.payment_requests} />
                <Block title="Links (not opened)" items={ex.urls} mono />
                <Block title="Contact channels" items={ex.contact_channels} mono />
              </div>
            </Section>
          </Rv>

          {ex.claims.length > 0 && (
            <Rv i={3}>
              <Section title="Claims in the message" hint="Each claim is checked against the bundled reference list where possible; otherwise it is marked unverified.">
                <ul className="space-y-2">
                  {ex.claims.map((c) => {
                    const st = CLAIM_STYLE[c.status];
                    return (
                      <li key={c.id} className="rounded-xl border border-ink-600 bg-ink-900/50 p-3 text-sm">
                        <div>{c.text}</div>
                        <div className={`mt-1 text-xs font-semibold ${st.c}`}>{st.t}</div>
                        {c.status_detail && <div className="mt-0.5 text-xs text-mist-400">{c.status_detail}</div>}
                      </li>
                    );
                  })}
                </ul>
              </Section>
            </Rv>
          )}
        </div>

        {/* 3. Verify before you act (visual climax) */}
        <div className="space-y-5 lg:col-span-2">
          <div className="space-y-5 lg:sticky lg:top-20">
            <Rv i={2}><VerifyPanel action={report.action} /></Rv>
            <Rv i={3}>
              <Section title="What is uncertain">
                <ul className="list-disc space-y-1.5 pl-5 text-sm text-mist-300">
                  {r.uncertainty_notes.length ? r.uncertainty_notes.map((n, i) => <li key={i}>{n}</li>) : <li>No specific gaps recorded.</li>}
                </ul>
              </Section>
            </Rv>
          </div>
        </div>
      </div>

      {report.extracted_text && (
        <Rv i={4}>
          <Section title="Text VERITAS read from your screenshot" hint="Check this against your image. If it is garbled or missing parts, the analysis is limited by OCR quality; try pasting the text instead. Shown for this request only and not saved.">
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-ink-950 p-3 font-mono text-xs text-mist-300">{report.extracted_text}</pre>
          </Section>
        </Rv>
      )}

      <Rv i={4}>
        <div className="grid gap-5 lg:grid-cols-2">
          <Section title="Analysis timeline" hint="Real step results and timings for this request.">
            <ResultTimeline steps={report.timeline} />
          </Section>
          <Section title="AI reasoning & provenance">
            {report.ai.used ? (
              <div className="space-y-2 text-sm text-mist-300">
                <div className="flex items-center gap-2"><ProvenanceBadge p="model_inference" /><span className="font-mono text-xs">{report.ai.provider}</span></div>
                {report.ai.summary && <p>{report.ai.summary}</p>}
                <p className="text-xs text-mist-400">Model output is schema-validated and quotes must appear verbatim in the message. It can add concern but never lower it, and it cannot change the verdict level on its own.</p>
              </div>
            ) : (
              <p className="text-sm text-mist-300">The AI reasoning layer was not used for this analysis ({report.ai.provider === "offline" ? "no provider configured" : "provider unavailable"}). Results come from deterministic security checks, which is why the same input always gives the same output.</p>
            )}
            {report.input.ocr_method && (
              <p className="mt-3 text-xs text-mist-400">Screenshot text via <span className="font-mono">{report.input.ocr_method}</span>.{report.input.ocr_note ? ` ${report.input.ocr_note}` : ""}</p>
            )}
            <p className="mt-3 break-all font-mono text-[11px] text-mist-500">request {report.request_id} · sha256 {report.input.sha256.slice(0, 16)}…</p>
          </Section>
        </div>
      </Rv>

      <Rv i={5}>
        <section className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
          <div className="text-mist-300">{fb ? <span className="animate-pop inline-block">Thanks — recorded as <b>{fb.replace(/_/g, " ")}</b>.</span> : "Did this help? Tell us how it turned out:"}</div>
          <div className="flex flex-wrap gap-2">
            <button className="btn-ghost !py-1.5" onClick={() => sendFeedback("was_scam")}>It was a scam</button>
            <button className="btn-ghost !py-1.5" onClick={() => sendFeedback("was_legitimate")}>It was legitimate</button>
            <button className="btn-ghost !py-1.5" onClick={() => sendFeedback("not_sure")}>Not sure</button>
          </div>
          {fbErr && <div className="w-full text-xs text-risk-high">Could not save feedback.</div>}
        </section>
        <p className="mt-4 text-xs text-mist-500">{report.disclaimer}</p>
      </Rv>

      {drawer && <EvidenceDrawer report={report} onClose={() => setDrawer(false)} />}
    </div>
  );
}

function Block({ title, items, mono, danger }: { title: string; items: string[]; mono?: boolean; danger?: boolean }) {
  return (
    <div>
      <div className={`label mb-1 ${danger && items.length ? "text-risk-high" : ""}`}>{title}</div>
      {items.length === 0 ? <div className="text-xs text-mist-500">None found</div> : (
        <ul className="space-y-1">
          {items.slice(0, 6).map((t, i) => <li key={i} className={`break-all text-mist-100 ${mono ? "font-mono text-xs" : ""}`}>{t}</li>)}
        </ul>
      )}
    </div>
  );
}
