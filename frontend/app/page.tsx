import Link from "next/link";
import HeroDemo from "@/components/HeroDemo";
import Reveal from "@/components/Reveal";
import { PROVENANCE } from "@/lib/provenance";
import type { Provenance } from "@/lib/types";

const steps = [
  ["Submit", "Paste a message, drop a screenshot, or enter a link."],
  ["Extract", "Entities, claims, links, deadlines and what is being asked of you."],
  ["Check", "Social-engineering rules, URL/domain signals and cross-checks run in parallel."],
  ["Explain", "Risk and confidence kept separate, every reason labelled by source."],
  ["Verify before you act", "A safe, independent route to confirm. Never the link in the message."],
];

const pillars = [
  ["Evidence, not vibes", "Each finding says where it came from: the message itself, a fixed rule, an outside source, or an AI inference.", "M9 12l2 2 4-4M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6l8-3z"],
  ["Honest about uncertainty", "When something can’t be checked, VERITAS says “Unable to independently verify” and tells you how to.", "M12 9v4m0 4h.01M10.3 3.9L2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"],
  ["Built for the moment", "The output is a plan: what to do now, what not to do, and who to report to.", "M13 10V3L4 14h7v7l9-11h-7z"],
];

export default function Landing() {
  return (
    <div className="space-y-24">
      {/* Hero */}
      <section className="relative -mx-5 overflow-hidden px-5 pb-6 pt-10">
        <div className="bg-grid pointer-events-none absolute inset-0" aria-hidden />
        <div className="pointer-events-none absolute -left-24 top-0 h-72 w-72 animate-float rounded-full bg-brand-500/20 blur-3xl" aria-hidden />
        <div className="pointer-events-none absolute -right-20 top-24 h-80 w-80 animate-floatSlow rounded-full bg-prov-rule/20 blur-3xl" aria-hidden />

        <div className="relative grid items-center gap-12 lg:grid-cols-2">
          <div>
            <div className="mb-5 inline-flex animate-fadeUp items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3 py-1 text-xs font-medium text-brand-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-500" /> Personal digital trust layer
            </div>
            <h1 className="animate-fadeUp text-5xl font-bold leading-[1.05] tracking-tight [animation-delay:80ms] sm:text-6xl">
              Verify <span className="text-gradient">before</span> you act.
            </h1>
            <p className="mt-5 max-w-xl animate-fadeUp text-lg text-mist-300 [animation-delay:160ms]">
              Got a message that asks you to click, pay, or share a code? VERITAS shows you the evidence, what it can and cannot
              verify, and the safest next step, instead of just guessing “scam or not”.
            </p>
            <div className="mt-8 flex animate-fadeUp flex-wrap items-center gap-3 [animation-delay:240ms]">
              <Link href="/analyze" className="btn-primary !px-6 !py-3 text-base">Check a message
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M5 12h14M13 6l6 6-6 6" /></svg>
              </Link>
              <Link href="/scenarios" className="btn-ghost !px-6 !py-3 text-base">Try a sample scenario</Link>
            </div>
            <p className="mt-4 animate-fadeUp text-xs text-mist-500 [animation-delay:320ms]">Links in your message are never opened. Raw message text is not stored.</p>
          </div>

          <div className="relative animate-fadeUp [animation-delay:200ms]">
            <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-tr from-brand-500/20 via-transparent to-prov-rule/20 blur-2xl" aria-hidden />
            <div className="relative"><HeroDemo /></div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section aria-labelledby="how">
        <Reveal><h2 id="how" className="mb-6 text-center text-sm font-semibold uppercase tracking-[0.2em] text-mist-400">How it works</h2></Reveal>
        <ol className="grid gap-3 md:grid-cols-5">
          {steps.map(([t, d], i) => (
            <li key={t}>
              <Reveal delay={i * 90} className="h-full">
                <div className="card card-hover h-full p-4">
                  <div className="mb-3 grid h-8 w-8 place-items-center rounded-lg bg-brand-500/15 font-mono text-xs font-bold text-brand-400">0{i + 1}</div>
                  <div className="font-semibold">{t}</div>
                  <p className="mt-1 text-sm text-mist-400">{d}</p>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
      </section>

      {/* Pillars */}
      <section className="grid gap-4 md:grid-cols-3">
        {pillars.map(([t, d, icon], i) => (
          <Reveal key={t} delay={i * 110}>
            <div className="card card-hover h-full p-6">
              <div className="mb-4 grid h-11 w-11 place-items-center rounded-xl bg-brand-500/10 text-brand-400">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d={icon} /></svg>
              </div>
              <div className="text-lg font-semibold">{t}</div>
              <p className="mt-1.5 text-sm leading-relaxed text-mist-400">{d}</p>
            </div>
          </Reveal>
        ))}
      </section>

      {/* Provenance */}
      <section>
        <Reveal>
          <div className="card p-8">
            <h2 className="text-2xl font-bold">Every conclusion shows its work</h2>
            <p className="mt-1 max-w-2xl text-mist-400">Four kinds of evidence, labelled everywhere you look. The AI can add concern, but only inspectable checks decide the verdict.</p>
            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {(Object.keys(PROVENANCE) as Provenance[]).map((p) => (
                <div key={p} className="rounded-xl border border-ink-600 bg-ink-900/50 p-4 transition hover:-translate-y-0.5 hover:border-brand-500/40">
                  <span className={`chip ${PROVENANCE[p].cls}`}>{PROVENANCE[p].label}</span>
                  <p className="mt-2 text-sm text-mist-400">{PROVENANCE[p].help}</p>
                </div>
              ))}
            </div>
          </div>
        </Reveal>
      </section>

      {/* CTA */}
      <Reveal>
        <section className="relative overflow-hidden rounded-3xl border border-brand-500/30 bg-brand-500/10 p-10 text-center">
          <div className="pointer-events-none absolute -top-20 left-1/2 h-48 w-96 -translate-x-1/2 rounded-full bg-brand-500/20 blur-3xl" aria-hidden />
          <h2 className="relative text-3xl font-bold">Not sure about a message?</h2>
          <p className="relative mx-auto mt-2 max-w-lg text-mist-300">Check it in seconds, then decide with evidence in front of you.</p>
          <Link href="/analyze" className="btn-primary relative mt-6 !px-7 !py-3 text-base">Open the analyzer</Link>
        </section>
      </Reveal>
    </div>
  );
}
