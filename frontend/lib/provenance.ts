import type { Provenance } from "./types";

// Plain data (no "use client") so both server and client components can import it.
export const PROVENANCE: Record<Provenance, { label: string; cls: string; help: string }> = {
  observed_input: { label: "Observed in message", cls: "prov-obs", help: "Text or data literally present in what you submitted." },
  deterministic_rule: { label: "Rule-based check", cls: "prov-rule", help: "A fixed, inspectable security rule produced this. Same input, same result." },
  external_evidence: { label: "External evidence", cls: "prov-ext", help: "Retrieved from an outside source at analysis time, with timestamp." },
  model_inference: { label: "AI inference", cls: "prov-ai", help: "An AI model's judgement. Validated, bounded, and never able to change the verdict level on its own." },
};
