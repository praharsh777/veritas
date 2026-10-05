"""Transparent weighted risk model. Risk and confidence are kept separate.

risk = 1 - prod(1 - w_i)   (diminishing returns; many weak signals never exceed strong ones by much)

This is a communication aid, NOT a calibrated probability of fraud.
"""
from __future__ import annotations

from ..schemas import Evidence, ExtractionResult, RiskAssessment, RiskFactor, TechnicalSignal, ThreatSignal

HIGH_THRESHOLD = 65
MID_THRESHOLD = 30

LABELS = {
    "high_risk": "High Risk",
    "needs_verification": "Needs Verification",
    "low_risk_signals": "Low-Risk Signals",
}


def score(
    threats: list[ThreatSignal],
    techs: list[TechnicalSignal],
    extraction: ExtractionResult,
    evidence: list[Evidence],
    text_len: int,
    ocr_used: bool,
    ai_used: bool,
    org_resolved: bool,
    unverified_org: bool,
) -> RiskAssessment:
    factors: list[RiskFactor] = []
    for t in threats:
        factors.append(RiskFactor(label=t.label, weight=t.weight, provenance=t.provenance, ref=t.id))
    # at most the two strongest technical signals per subject, to avoid double counting one link
    by_subject: dict[str, list[TechnicalSignal]] = {}
    for s in techs:
        by_subject.setdefault(s.subject, []).append(s)
    for sigs in by_subject.values():
        for s in sorted(sigs, key=lambda x: -x.weight)[:2]:
            factors.append(RiskFactor(label=s.label, weight=s.weight, provenance=s.provenance, ref=s.id))

    def combine(fs) -> int:
        p = 1.0
        for f in fs:
            p *= 1.0 - min(max(f.weight, 0.0), 0.6)
        return int(round(min(0.98, 1.0 - p) * 100))

    # The verdict LEVEL is decided by deterministic evidence only. AI inferences may nudge the number
    # upward inside the level but can never move a message into a higher level on their own.
    det = [f for f in factors if f.provenance != "model_inference"]
    ai = [f for f in factors if f.provenance == "model_inference"]
    det_risk = combine(det)
    # a message that asks for secrets, or for money through hard-to-reverse channels, is never "low"
    critical_ids = {"credential_otp_request", "remote_access_request", "payment_redirection", "unconventional_payment", "advance_fee"}
    if any(f.ref in critical_ids for f in det):
        det_risk = max(det_risk, 45)

    # gift-card / crypto / wire demands combined with pressure or secrecy are the signature of classic scams
    refs = {f.ref for f in det}
    if "unconventional_payment" in refs and refs & {"urgency", "secrecy_isolation", "fear_punishment"}:
        det_risk = max(det_risk, HIGH_THRESHOLD)

    level = "high_risk" if det_risk >= HIGH_THRESHOLD else "needs_verification" if det_risk >= MID_THRESHOLD else "low_risk_signals"
    risk = max(det_risk, combine(factors))
    ceiling = {"high_risk": 98, "needs_verification": HIGH_THRESHOLD - 1, "low_risk_signals": MID_THRESHOLD - 1}[level]
    ai_capped = risk > ceiling
    risk = min(risk, ceiling)

    # ---- confidence: how much *independent* evidence supports this assessment ----
    categories = {f.ref.split("_")[0] for f in factors}
    conf = 35 + min(len(categories), 6) * 6
    notes: list[str] = []
    if any(e.kind == "bundled_reference" and e.outcome in ("consistent", "inconsistent") for e in evidence):
        conf += 12
    else:
        notes.append("No organization could be matched against the bundled reference list, so identity could not be checked.")
    if extraction.urls and techs:
        conf += 8
    if any(e.kind == "live_check" for e in evidence):
        conf += 8
    if any(f.provenance == "deterministic_rule" and f.weight >= 0.3 for f in factors):
        conf += 8
    if ai_used:
        conf += 5
    else:
        notes.append("AI reasoning layer was not used for this analysis (deterministic checks only).")
    if text_len < 60:
        conf -= 20
        notes.append("Very little text was provided, which limits what can be assessed.")
    if ocr_used:
        conf -= 6
        notes.append("Text came from a screenshot via OCR; misread characters are possible.")
    if unverified_org:
        notes.append("Unable to independently verify the sender's claimed identity without contacting them through an official channel.")
    if not factors:
        notes.append("No scam indicators were detected. That is not proof the message is genuine.")
    conf = max(5, min(95, conf))

    if ai_capped:
        notes.append("AI-identified signals suggest additional concern, but the verdict level is set by rule-based and observed evidence only.")
    if level == "high_risk" and conf < 55:
        notes.insert(0, "High concern, but verification is incomplete.")

    factors.sort(key=lambda f: -f.weight)
    return RiskAssessment(
        risk_score=risk,
        risk_level=level,
        verdict_label=LABELS[level],
        confidence_score=conf,
        top_factors=factors[:6],
        uncertainty_notes=notes,
    )
