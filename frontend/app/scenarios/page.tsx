"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Scenario } from "@/lib/types";
import { Empty, ErrorBanner, Spinner } from "@/components/ui";

export default function ScenariosPage() {
  const router = useRouter();
  const [items, setItems] = useState<Scenario[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => { api.scenarios().then(setItems).catch((e) => setError(e instanceof ApiError ? e.message : "Could not load scenarios.")); }, []);

  async function run(s: Scenario, asImage: boolean) {
    setBusy(s.id + (asImage ? ":img" : "")); setError(null);
    try {
      let rep;
      if (asImage) {
        const blob = await fetch(`/api/scenarios/${s.id}/screenshot`).then((r) => { if (!r.ok) throw new ApiError("Demo screenshot unavailable.", r.status); return r.blob(); });
        rep = await api.analyzeFile(blob, `${s.id}.png`);
      } else rep = await api.analyzeScenario(s.id);
      router.push(`/report/${rep.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Analysis failed.");
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Scenario gallery</h1>
        <p className="text-sm text-mist-400">Realistic, fictional examples. Each runs through exactly the same engine as your own input.</p>
      </div>
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      {!items && !error && (
        <div className="grid gap-4 md:grid-cols-2" aria-busy="true">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-44 w-full" />)}</div>
      )}
      {items && items.length === 0 && <Empty title="No scenarios" body="The backend returned no scenarios." />}
      <div className="grid gap-4 md:grid-cols-2">
        {items?.map((s, i) => (
          <article key={s.id} style={{ animationDelay: `${i * 60}ms` }} className="card card-hover stagger group flex gap-4 p-5">
            {s.has_screenshot && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`/api/scenarios/${s.id}/screenshot`} alt={`Demo screenshot: ${s.title}`} loading="lazy"
                className="hidden h-36 w-24 shrink-0 rounded-lg border border-ink-600 bg-ink-900 object-cover object-top transition duration-300 group-hover:scale-[1.04] group-hover:border-brand-500/50 sm:block" />
            )}
            <div className="flex min-w-0 flex-1 flex-col">
              <div className="flex items-center gap-2"><span className="chip border-ink-500 text-mist-400">{s.channel}</span></div>
              <h2 className="mt-1.5 font-semibold">{s.title}</h2>
              <p className="text-sm text-mist-400">{s.blurb}</p>
              <p className="mt-2 line-clamp-3 font-mono text-xs text-mist-500">{s.text}</p>
              <div className="mt-auto flex flex-wrap gap-2 pt-4">
                <button className="btn-primary !py-1.5" disabled={!!busy} onClick={() => run(s, false)}>
                  {busy === s.id ? <><Spinner /> Analyzing…</> : "Analyze text"}
                </button>
                {s.has_screenshot && (
                  <button className="btn-ghost !py-1.5" disabled={!!busy} onClick={() => run(s, true)}>
                    {busy === s.id + ":img" ? <><Spinner /> Reading…</> : "Analyze as screenshot"}
                  </button>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
