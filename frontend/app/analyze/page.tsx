"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AnalysisReport, Scenario } from "@/lib/types";
import ReportView from "@/components/ReportView";
import { LiveTimeline, ResultTimeline } from "@/components/Timeline";
import { ErrorBanner, ReportSkeleton, Spinner } from "@/components/ui";

type Mode = "text" | "url" | "file";
const MAX_IMG = 6 * 1024 * 1024;

export default function AnalyzePage() {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [samples, setSamples] = useState<Scenario[]>([]);
  const [drag, setDrag] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => { api.scenarios().then(setSamples).catch(() => setSamples([])); }, []);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const pickFile = useCallback((f: File | null) => {
    setError(null);
    if (!f) return;
    const okType = /^image\/(png|jpe?g|webp)$/.test(f.type) || /\.(txt|eml|md)$/i.test(f.name);
    if (!okType) { setError("Unsupported file. Use a PNG/JPEG/WebP screenshot or a .txt/.eml file."); return; }
    if (f.size > MAX_IMG) { setError("File is too large (max 6 MB)."); return; }
    setFile(f);
    setPreview((old) => { if (old) URL.revokeObjectURL(old); return f.type.startsWith("image/") ? URL.createObjectURL(f) : null; });
  }, []);

  const canSubmit = !busy && ((mode === "text" && text.trim().length >= 3) || (mode === "url" && url.trim().length >= 3) || (mode === "file" && !!file));

  async function submit() {
    setBusy(true); setError(null); setReport(null);
    try {
      const r = mode === "text" ? await api.analyzeText(text) : mode === "url" ? await api.analyzeUrl(url.trim()) : await api.analyzeFile(file!);
      setReport(r);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong. Please try again.");
    } finally { setBusy(false); }
  }

  const tabs: [Mode, string][] = [["text", "Message"], ["url", "Link"], ["file", "Screenshot / file"]];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Analyze workspace</h1>
        <p className="text-sm text-mist-400">Submit something suspicious. Nothing in it is opened, clicked, or run.</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-5">
        <section className="card p-5 lg:col-span-3" aria-label="Input">
          <div role="tablist" className="mb-4 inline-flex rounded-xl border border-ink-600 bg-ink-900 p-1">
            {tabs.map(([m, l]) => (
              <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)}
                className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all duration-200 ${mode === m ? "bg-brand-500/15 text-brand-400 shadow-sm" : "text-mist-400 hover:text-mist-100"}`}>{l}</button>
            ))}
          </div>

          {mode === "text" && (
            <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={20000} rows={11}
              placeholder="Paste the message, email, or chat here…" aria-label="Message text"
              className="w-full resize-y rounded-xl border border-ink-500 bg-ink-900 p-4 text-sm leading-relaxed outline-none focus:border-brand-400" />
          )}
          {mode === "url" && (
            <div>
              <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://… (the link is analysed, never opened)" aria-label="Link"
                className="w-full rounded-xl border border-ink-500 bg-ink-900 p-4 font-mono text-sm outline-none focus:border-brand-400" />
              <p className="mt-2 text-xs text-mist-400">Checks the address itself: look-alike names, odd domains, shorteners, and mismatches.</p>
            </div>
          )}
          {mode === "file" && (
            <div
              onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
              onDrop={(e) => { e.preventDefault(); setDrag(false); pickFile(e.dataTransfer.files?.[0] ?? null); }}
              className={`grid min-h-[16rem] place-items-center rounded-xl border-2 border-dashed p-6 text-center transition ${drag ? "border-brand-400 bg-brand-500/5" : "border-ink-500"}`}>
              {file ? (
                <div className="space-y-3">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {preview && <img src={preview} alt="Selected screenshot" className="mx-auto max-h-56 rounded-lg border border-ink-600" />}
                  <div className="font-mono text-xs text-mist-300">{file.name} · {(file.size / 1024).toFixed(0)} KB</div>
                  <button className="btn-ghost !py-1.5" onClick={() => { setFile(null); setPreview(null); }}>Remove</button>
                </div>
              ) : (
                <div>
                  <div className="font-medium">Drop a screenshot or document here</div>
                  <p className="mt-1 text-sm text-mist-400">PNG, JPEG, WebP (max 6 MB) · .txt / .eml</p>
                  <label className="btn-ghost mt-4 cursor-pointer">Choose file
                    <input type="file" accept="image/png,image/jpeg,image/webp,.txt,.eml,.md" className="sr-only" onChange={(e) => pickFile(e.target.files?.[0] ?? null)} />
                  </label>
                </div>
              )}
            </div>
          )}

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2 text-xs text-mist-400">
              {samples.length > 0 && mode === "text" && <>
                <span>Try a sample:</span>
                {samples.slice(0, 4).map((s) => (
                  <button key={s.id} onClick={() => setText(s.text)} className="chip border-ink-500 transition hover:-translate-y-0.5 hover:border-brand-400 hover:text-mist-100">{s.title}</button>
                ))}
              </>}
            </div>
            <button className="btn-primary" disabled={!canSubmit} onClick={submit}>
              {busy ? <><Spinner /> Analyzing…</> : "Verify"}
            </button>
          </div>
          {error && <div className="mt-4"><ErrorBanner message={error} onClose={() => setError(null)} /></div>}
        </section>

        <aside className="card p-5 lg:col-span-2" aria-label="Analysis timeline">
          <div className="label mb-3">Analysis timeline</div>
          {report && !busy ? <ResultTimeline steps={report.timeline} /> : <LiveTimeline running={busy} />}
          {!busy && !report && <p className="mt-4 text-xs text-mist-500">Checks run in parallel once you submit: social engineering, links and domains, identity cross-check, and optional AI reasoning.</p>}
          {report && !busy && report.threat_signals.length + report.technical_signals.length > 0 && (
            <div className="mt-5 border-t border-ink-600 pt-4">
              <div className="label mb-2">Detected indicators</div>
              <div className="flex flex-wrap gap-1.5">
                {[...report.threat_signals.map((t) => t.label), ...report.technical_signals.map((t) => t.label)].slice(0, 10).map((l, i) => (
                  <span key={i} className="chip border-ink-500 text-mist-300">{l}</span>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      <div ref={resultRef} className="scroll-mt-20">
        {busy && <ReportSkeleton />}
        {!busy && report && <ReportView key={report.id} report={report} />}
      </div>
    </div>
  );
}
