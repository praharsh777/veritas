export type Provenance = "observed_input" | "deterministic_rule" | "external_evidence" | "model_inference";
export type RiskLevel = "high_risk" | "needs_verification" | "low_risk_signals";

export interface ThreatSignal { id: string; label: string; weight: number; explanation: string; excerpts: string[]; provenance: Provenance }
export interface TechnicalSignal { id: string; label: string; weight: number; detail: string; subject: string; provenance: Provenance }
export interface Evidence {
  id: string; kind: "bundled_reference" | "live_check"; title: string; source_url: string | null; retrieved_at: string;
  supports: string; outcome: "consistent" | "inconsistent" | "informational"; limitations: string; provenance: Provenance;
}
export interface Claim {
  id: string; text: string; entity: string | null; verifiable: boolean;
  status: "consistent_with_reference" | "inconsistent_with_reference" | "unable_to_verify";
  status_detail: string; evidence_ids: string[]; provenance: Provenance;
}
export interface RiskFactor { label: string; weight: number; provenance: Provenance; ref: string }
export interface RiskAssessment {
  risk_score: number; risk_level: RiskLevel; verdict_label: string; confidence_score: number;
  top_factors: RiskFactor[]; uncertainty_notes: string[]; score_disclaimer: string;
}
export interface VerificationStep { order: number; title: string; detail: string; route: string | null; status: "recommended" | "unable_to_verify" }
export interface ActionRecommendation { headline: string; do_now: string[]; do_not: string[]; verification_steps: VerificationStep[]; report_to: string[] }
export interface TimelineStep { id: string; label: string; status: "done" | "skipped" | "failed"; duration_ms: number; detail: string }
export interface ExtractionResult {
  entities: { name: string; type: string }[]; urls: string[]; claims: Claim[];
  requested_actions: { action: string; label: string; excerpt: string }[];
  requested_data: { data_type: string; label: string; excerpt: string }[];
  deadlines: string[]; payment_requests: string[]; authority_claims: string[]; contact_channels: string[];
}
export interface AnalysisReport {
  id: string; created_at: string; request_id: string;
  input: { kind: string; source_filename: string | null; sha256: string; char_count: number; preview: string; ocr_method: string | null; ocr_note: string | null };
  category: string; category_label: string; summary: string; extraction: ExtractionResult;
  threat_signals: ThreatSignal[]; technical_signals: TechnicalSignal[]; evidence: Evidence[];
  risk: RiskAssessment;
  ai: {
    used: boolean; provider: string; summary: string | null; notes: string[]; configured: boolean;
    assessment: "likely_legitimate" | "unclear" | "suspicious" | "likely_scam" | null;
    observations: string[]; suggested_checks: string[]; error: string | null; can_retry: boolean;
  };
  action: ActionRecommendation; timeline: TimelineStep[]; disclaimer: string; feedback: string | null; extracted_text?: string | null;
}
export interface IncidentRow {
  id: string; created_at: string; category: string; category_label: string; risk_score: number;
  risk_level: RiskLevel; confidence: number; kind: string; preview: string; feedback: string | null;
}
export interface Scenario { id: string; title: string; channel: string; blurb: string; text: string; has_screenshot: boolean }
export interface Health { status: string; ai_provider: string; ai_enabled: boolean; live_url_checks: boolean; vision_ocr: boolean }
