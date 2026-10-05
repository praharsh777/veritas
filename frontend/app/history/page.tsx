"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { IncidentRow } from "@/lib/types";
import { Empty, ErrorBanner, LevelPill, timeAgo } from "@/components/ui";

const LABEL = { high_risk: "High Risk", needs_verification: "Needs Verification", low_risk_signals: "Low-Risk Signals" } as const;

export default function HistoryPage() {
  const [rows, setRows] = useState<IncidentRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.incidents().then(setRows).catch((e) => setError(e instanceof ApiError ? e.message : "Could not load history."));
  useEffect(() => { load(); }, []);

  async function clearAll() {
    if (!confirm("Delete all saved incident reports? This cannot be undone.")) return;
    try { await api.clearIncidents(); setRows([]); } catch (e) { setError(e instanceof ApiError ? e.message : "Could not clear history."); }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Incident history</h1>
          <p className="text-sm text-mist-400">Previous analyses. Only a redacted preview is kept — never the raw message.</p>
        </div>
        {rows && rows.length > 0 && <button className="btn-ghost" onClick={clearAll}>Clear all</button>}
      </div>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {!rows && !error && (
        <div className="space-y-3" aria-busy="true">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-20 w-full" />)}</div>
      )}
      {rows && rows.length === 0 && (
        <Empty title="No analyses yet" body="Run an analysis or try a sample scenario and it will appear here.">
          <Link href="/scenarios" className="btn-primary mt-3">Open scenario gallery</Link>
        </Empty>
      )}
      {rows && rows.length > 0 && (
        <ul className="space-y-3">
          {rows.map((r, i) => (
            <li key={r.id} className="stagger" style={{ animationDelay: `${Math.min(i, 10) * 50}ms` }}>
              <Link href={`/report/${r.id}`} className="card card-hover flex flex-wrap items-center justify-between gap-3 p-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <LevelPill level={r.risk_level} label={LABEL[r.risk_level]} />
                    <span className="text-sm font-medium">{r.category_label}</span>
                    <span className="text-xs text-mist-500">{timeAgo(r.created_at)}</span>
                  </div>
                  <p className="mt-1.5 truncate font-mono text-xs text-mist-400">{r.preview}</p>
                </div>
                <div className="flex items-center gap-4 text-xs text-mist-400">
                  <span>Risk <b className="font-mono text-mist-100">{r.risk_score}</b></span>
                  <span>Conf <b className="font-mono text-mist-100">{r.confidence}</b></span>
                  <span className="chip border-ink-500">{r.feedback ? r.feedback.replace(/_/g, " ") : "no feedback"}</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
