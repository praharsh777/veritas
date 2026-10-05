"use client";
import { useEffect } from "react";
import type { AnalysisReport, Evidence } from "@/lib/types";
import { ProvenanceBadge, timeAgo } from "./ui";

const OUTCOME: Record<Evidence["outcome"], { text: string; cls: string }> = {
  consistent: { text: "Consistent with reference", cls: "text-risk-low" },
  inconsistent: { text: "Does not match reference", cls: "text-risk-high" },
  informational: { text: "Informational", cls: "text-mist-300" },
};

export default function EvidenceDrawer({ report, onClose, focusId }: { report: AnalysisReport; onClose: () => void; focusId?: string }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const ev = report.evidence;
  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-modal="true" aria-label="Evidence">
      <div className="absolute inset-0 animate-fadeIn bg-ink-950/70 backdrop-blur-sm" onClick={onClose} />
      <aside className="absolute right-0 top-0 h-full w-full max-w-lg animate-slideIn overflow-y-auto border-l border-ink-600 bg-ink-900 p-6 shadow-2xl">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Evidence</h2>
            <p className="text-sm text-mist-400">What was checked, against what, when, and what remains uncertain.</p>
          </div>
          <button onClick={onClose} className="btn-ghost !px-3 !py-1.5" aria-label="Close evidence drawer">Close</button>
        </div>

        {ev.length === 0 && (
          <div className="rounded-xl border border-ink-600 bg-ink-800 p-4 text-sm text-mist-300">
            <b>Unable to independently verify.</b> No organization in this message matched the bundled reference list, and no live
            checks were run. VERITAS will not claim any outside confirmation it does not have.
          </div>
        )}

        <ul className="space-y-3">
          {ev.map((e, idx) => (
            <li key={e.id} style={{ animationDelay: `${120 + idx * 70}ms` }} className={`stagger rounded-xl border p-4 ${focusId === e.id ? "border-brand-400" : "border-ink-600"} bg-ink-800`}>
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className={`text-xs font-semibold ${OUTCOME[e.outcome].cls}`}>{OUTCOME[e.outcome].text}</span>
                <span className="chip border-ink-500 text-mist-300">{e.kind === "bundled_reference" ? "Bundled reference (not live)" : "Live check"}</span>
                <ProvenanceBadge p={e.provenance} />
              </div>
              <div className="text-sm font-medium">{e.title}</div>
              <dl className="mt-2 space-y-1.5 text-xs text-mist-300">
                <div><dt className="label inline">Supports: </dt><dd className="inline">{e.supports}</dd></div>
                <div><dt className="label inline">Retrieved: </dt><dd className="inline">{timeAgo(e.retrieved_at)}</dd></div>
                {e.source_url && <div><dt className="label inline">Reference point: </dt><dd className="inline font-mono">{e.source_url.replace(/^https?:\/\//, "")}</dd></div>}
                <div className="text-mist-400"><dt className="label inline">Limits: </dt><dd className="inline">{e.limitations}</dd></div>
              </dl>
            </li>
          ))}
        </ul>

        {report.risk.uncertainty_notes.length > 0 && (
          <div className="mt-6">
            <div className="label mb-2">Still uncertain</div>
            <ul className="list-disc space-y-1 pl-5 text-sm text-mist-300">
              {report.risk.uncertainty_notes.map((n, i) => <li key={i}>{n}</li>)}
            </ul>
          </div>
        )}
      </aside>
    </div>
  );
}
