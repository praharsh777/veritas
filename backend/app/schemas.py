"""Typed schemas for every analysis artifact. Every conclusion carries provenance."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

Provenance = Literal["observed_input", "deterministic_rule", "external_evidence", "model_inference"]
RiskLevel = Literal["high_risk", "needs_verification", "low_risk_signals"]
Category = Literal[
    "bank_account_alert",
    "job_offer",
    "tech_support",
    "invoice_payment",
    "delivery",
    "impersonation",
    "prize_lure",
    "unclassified",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class InputArtifact(BaseModel):
    kind: Literal["text", "url", "image", "document"]
    source_filename: Optional[str] = None
    sha256: str
    char_count: int
    preview: str = Field(description="Redacted, truncated preview. Raw content is not persisted.")
    ocr_method: Optional[str] = None
    ocr_note: Optional[str] = None


class ExtractedEntity(BaseModel):
    name: str
    type: Literal["organization", "person_role", "email", "phone", "domain", "money"]
    provenance: Provenance = "observed_input"
    registry_key: Optional[str] = None
    claimed: bool = Field(default=False, description="Message presents itself as coming from this organization (vs. merely mentioning it)")


class Claim(BaseModel):
    id: str
    text: str
    entity: Optional[str] = None
    verifiable: bool = True
    status: Literal["consistent_with_reference", "inconsistent_with_reference", "unable_to_verify"] = (
        "unable_to_verify"
    )
    status_detail: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = "observed_input"


class RequestedAction(BaseModel):
    action: str
    label: str
    excerpt: str
    provenance: Provenance = "observed_input"


class RequestedData(BaseModel):
    data_type: str
    label: str
    excerpt: str
    sensitive: bool = True
    provenance: Provenance = "observed_input"


class ExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    requested_actions: list[RequestedAction] = Field(default_factory=list)
    requested_data: list[RequestedData] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    payment_requests: list[str] = Field(default_factory=list)
    authority_claims: list[str] = Field(default_factory=list)
    contact_channels: list[str] = Field(default_factory=list)


class ThreatSignal(BaseModel):
    id: str
    label: str
    weight: float = Field(ge=0, le=1)
    explanation: str
    excerpts: list[str] = Field(default_factory=list)
    provenance: Provenance = "deterministic_rule"


class TechnicalSignal(BaseModel):
    id: str
    label: str
    weight: float = Field(ge=0, le=1)
    detail: str
    subject: str = Field(description="The URL / domain / email the signal is about")
    provenance: Provenance = "deterministic_rule"


class Evidence(BaseModel):
    id: str
    kind: Literal["bundled_reference", "live_check"]
    title: str
    source_url: Optional[str] = None
    retrieved_at: str
    supports: str = Field(description="The exact claim or conclusion this evidence relates to")
    outcome: Literal["consistent", "inconsistent", "informational"]
    limitations: str
    provenance: Provenance = "deterministic_rule"


class RiskFactor(BaseModel):
    label: str
    weight: float
    provenance: Provenance
    ref: str = Field(description="id of the signal this factor came from")


class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    verdict_label: str
    confidence_score: int = Field(ge=0, le=100)
    top_factors: list[RiskFactor] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    score_disclaimer: str = (
        "The risk score is a transparent weighted communication aid, not a calibrated probability of fraud."
    )


class VerificationStep(BaseModel):
    order: int
    title: str
    detail: str
    route: Optional[str] = Field(default=None, description="Safe destination the USER should type/open themselves")
    status: Literal["recommended", "unable_to_verify"] = "recommended"


class ActionRecommendation(BaseModel):
    headline: str
    do_now: list[str] = Field(default_factory=list)
    do_not: list[str] = Field(default_factory=list)
    verification_steps: list[VerificationStep] = Field(default_factory=list)
    report_to: list[str] = Field(default_factory=list)


class AIReasoning(BaseModel):
    used: bool
    provider: str
    summary: Optional[str] = None
    notes: list[str] = Field(default_factory=list)
    configured: bool = False
    assessment: Optional[str] = None
    observations: list[str] = Field(default_factory=list)
    suggested_checks: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    can_retry: bool = False


class TimelineStep(BaseModel):
    id: str
    label: str
    status: Literal["done", "skipped", "failed"]
    duration_ms: int
    detail: str = ""


class AnalysisReport(BaseModel):
    id: str
    created_at: str
    request_id: str
    input: InputArtifact
    category: Category
    category_label: str
    summary: str
    extraction: ExtractionResult
    threat_signals: list[ThreatSignal]
    technical_signals: list[TechnicalSignal]
    evidence: list[Evidence]
    risk: RiskAssessment
    ai: AIReasoning
    action: ActionRecommendation
    timeline: list[TimelineStep]
    disclaimer: str
    feedback: Optional[str] = None
    # Text read from a screenshot/document, returned only in the live response (never persisted).
    extracted_text: Optional[str] = None


# ---- API request models ----
class AnalyzeRequest(BaseModel):
    text: Optional[str] = Field(default=None, max_length=25_000)
    url: Optional[str] = Field(default=None, max_length=2048)
    scenario_id: Optional[str] = Field(default=None, max_length=64)


class FeedbackRequest(BaseModel):
    outcome: Literal["was_scam", "was_legitimate", "not_sure"]
    note: Optional[str] = Field(default=None, max_length=500)
