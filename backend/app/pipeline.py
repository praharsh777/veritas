"""End-to-end analysis pipeline.

INPUT → NORMALIZE → EXTRACT → PARALLEL ANALYSIS → EVIDENCE/CROSS-CHECK → RISK MODEL → EXPLANATION → ACTION PLAN
"""
from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import Awaitable, Callable, Optional

from .analysis import actions, extraction as ext, scoring, signals as sigs, technical
from .config import settings
from .providers.base import LLMProvider, ProviderError
from .schemas import (
    AIReasoning,
    AnalysisReport,
    InputArtifact,
    TechnicalSignal,
    ThreatSignal,
    TimelineStep,
    utcnow,
)
from .security.sanitize import normalize_text, redact_preview, sha256_hex
from .verification import verify
from .verification.registry import ORG_BY_KEY

DISCLAIMER = (
    "VERITAS is a safety aid. It is not a law-enforcement, banking, or cybersecurity authority and cannot guarantee "
    "that any message is genuine or fraudulent. When in doubt, contact the organization through a channel you already trust."
)


import collections as _collections

_RECENT: "_collections.OrderedDict[str, tuple[float, dict]]" = _collections.OrderedDict()
_RECENT_MAX, _RECENT_TTL = 40, 30 * 60


def remember(report_id: str, args: dict) -> None:
    """Keep the analysed text IN MEMORY ONLY (never on disk) for a short time so 'Retry AI' can re-run it."""
    now = time.time()
    _RECENT[report_id] = (now, args)
    while len(_RECENT) > _RECENT_MAX or (_RECENT and now - next(iter(_RECENT.values()))[0] > _RECENT_TTL):
        _RECENT.popitem(last=False)


def recall(report_id: str) -> Optional[dict]:
    item = _RECENT.get(report_id)
    if item and time.time() - item[0] <= _RECENT_TTL:
        return item[1]
    return None


async def _timed(label: str, fn: Callable[[], Awaitable | object], timeline: list[TimelineStep], id_: str, detail_fn=None):
    t0 = time.perf_counter()
    status, result, err = "done", None, None
    try:
        r = fn()
        result = await r if asyncio.iscoroutine(r) else r
    except Exception as e:  # tool failure → fail safely, never crash the analysis
        status, err = "failed", e
    ms = int((time.perf_counter() - t0) * 1000)
    detail = ""
    if status == "failed":
        detail = "This check failed and was skipped; results below do not include it."
    elif detail_fn:
        detail = detail_fn(result)
    timeline.append(TimelineStep(id=id_, label=label, status=status, duration_ms=ms, detail=detail))  # type: ignore[arg-type]
    return result, err


def _summary_for_llm(e) -> str:
    return (
        f"orgs={[x.name for x in e.entities if x.type == 'organization']}; urls={e.urls[:5]}; "
        f"requested_actions={[a.action for a in e.requested_actions]}; requested_data={[d.data_type for d in e.requested_data]}; "
        f"deadlines={e.deadlines[:3]}"
    )


def _dangerous_scheme_signal(url: str) -> Optional[TechnicalSignal]:
    m = re.match(r"(?i)^\s*([a-z][a-z0-9+.-]*):", url)
    if m and m.group(1).lower() in ("javascript", "data", "file", "vbscript", "blob", "ftp", "intent", "chrome", "about"):
        return TechnicalSignal(
            id="dangerous_scheme", label="Link uses a non-web scheme", weight=0.5,
            detail=f"The scheme '{m.group(1).lower()}:' can run code or read local files; it is not a normal web link.",
            subject=url[:200],
        )
    return None


async def analyze(
    text: str,
    kind: str,
    provider: LLMProvider,
    request_id: str,
    source_filename: str | None = None,
    ocr_method: str | None = None,
    ocr_note: str | None = None,
    raw_url: str | None = None,
) -> AnalysisReport:
    timeline: list[TimelineStep] = []
    t0 = time.perf_counter()

    # 1. normalize
    norm = normalize_text(text, settings.max_text_chars)
    timeline.append(TimelineStep(id="normalize", label="Normalize & sanitize input", status="done",
                                 duration_ms=int((time.perf_counter() - t0) * 1000),
                                 detail=f"{len(norm)} characters; control/hidden characters removed."))

    # 2. extract
    pre_urls = [raw_url] if raw_url else []
    extraction, _ = await _timed("Extract entities, claims & requests", lambda: ext.extract(norm, pre_urls), timeline, "extract",
                                 lambda r: f"{len(r.entities)} entities, {len(r.urls)} links, {len(r.requested_actions)} requested actions.")
    if extraction is None:  # extraction itself failed: continue with empty structure
        from .schemas import ExtractionResult
        extraction = ExtractionResult()

    claimed_orgs = [ORG_BY_KEY[e.registry_key] for e in extraction.entities if e.registry_key and e.claimed]

    def tech_job():
        out: list[TechnicalSignal] = []
        for u in extraction.urls:
            d = _dangerous_scheme_signal(u) if raw_url else None
            if d:
                out.append(d)
                continue
            out += technical.analyze_url(u, claimed_orgs)
        for e in extraction.entities:
            if e.type == "email":
                out += technical.analyze_email(e.name, claimed_orgs)
        # sender claims to represent an organization we cannot look up, but writes from a free mail service
        unknown = [e for e in extraction.entities if e.type == "organization" and e.registry_key is None and e.claimed]
        emails = [e.name for e in extraction.entities if e.type == "email"]
        if unknown and not claimed_orgs and emails:
            from .verification.registry import FREEMAIL_DOMAINS
            m = re.search(r"(?im)^\s*from:.*?([\w.%+-]+@[\w.-]+\.\w+)", norm)
            sender = m.group(1) if m else emails[0]
            if technical.registrable_domain(sender.split("@")[-1].lower()) in FREEMAIL_DOMAINS:
                out.append(TechnicalSignal(
                    id="freemail_for_org", label="Claims to represent a company but writes from a free email address", weight=0.3,
                    detail=f"The sender says they represent {unknown[0].name}, but the address {sender} is on a free email provider, "
                           "not the company's own domain. Companies normally write from their own domain.",
                    subject=sender))
        return out

    async def ai_job():
        if not provider.available:
            return None
        return await provider.analyze(norm, _summary_for_llm(extraction))

    # 3. parallel analysis
    (threats, _), (techs, _), (ai_out, ai_err) = await asyncio.gather(
        _timed("Social-engineering signals", lambda: sigs.detect_threat_signals(norm, extraction), timeline, "social",
               lambda r: f"{len(r)} manipulation pattern(s) found."),
        _timed("URL, domain & sender checks", tech_job, timeline, "technical",
               lambda r: f"{len(r)} technical signal(s) across {len(extraction.urls)} link(s)."),
        _timed("AI reasoning", ai_job, timeline, "ai",
               lambda r: "Skipped: no AI provider configured." if not provider.available else
               ("Model returned a validated analysis." if r else "No additional model findings.")),
    )
    threats = threats or []
    techs = techs or []
    if not provider.available:
        for s in timeline:
            if s.id == "ai":
                s.status = "skipped"

    # merge validated AI signals (capped, can only add concern)
    ai_notes: list[str] = []
    ai_summary = None
    if ai_err is not None:
        reason = str(ai_err) if isinstance(ai_err, ProviderError) else type(ai_err).__name__
        ai_notes.append(f"AI reasoning failed ({reason}); analysis continued with deterministic checks only.")
        import logging
        logging.getLogger("veritas").warning("ai provider failure rid=%s reason=%s", request_id, reason)
    if ai_out is not None:
        ai_summary = ai_out.intent_summary or None
        have = {t.id for t in threats}
        added = 0.0
        for s in ai_out.additional_signals:
            if s.id in have or added >= 0.25:
                continue
            w = min(0.12, 0.25 - added)
            added += w
            threats.append(ThreatSignal(id=s.id, label=s.id.replace("_", " ").capitalize() + " (AI-identified)",
                                        weight=w, explanation=s.explanation, excerpts=[s.excerpt],
                                        provenance="model_inference"))
        ai_notes += [f"Model uncertainty: {u}" for u in ai_out.uncertainties[:3]]

    # 4. evidence / cross-check
    (cc, _) = await _timed("Cross-check against reference data", lambda: verify.cross_check(extraction), timeline, "evidence",
                           lambda r: f"{len(r[0])} evidence item(s); organization "
                                     f"{'matched' if r[1] else 'not matched'} to bundled reference.")
    evidence, org_resolved, unverified_org = cc if cc else ([], False, False)

    live_failures: list[str] = []
    if settings.live_url_checks and extraction.urls:
        (lv, _) = await _timed("Live link inspection (SSRF-guarded)", lambda: verify.live_checks(extraction.urls), timeline, "live",
                               lambda r: f"{len(r[0])} redirect chain(s) inspected.")
        if lv:
            evidence += lv[0]
            live_failures = lv[1]
    else:
        timeline.append(TimelineStep(id="live", label="Live link inspection", status="skipped", duration_ms=0,
                                     detail="Disabled by default for safety (set ENABLE_LIVE_URL_CHECKS=true)."))

    # 5. risk model
    risk = scoring.score(threats, techs, extraction, evidence, len(norm), ocr_method is not None and ocr_method != "demo_fixture" and ocr_method != "text",
                         ai_out is not None, org_resolved, unverified_org)
    risk.uncertainty_notes += ai_notes + live_failures
    timeline.append(TimelineStep(id="risk", label="Risk & confidence model", status="done", duration_ms=0,
                                 detail=f"Risk {risk.risk_score}/100, confidence {risk.confidence_score}/100 (kept separate)."))

    # 6. category + action plan
    category = actions.classify(norm, threats)
    plan = actions.build_action_plan(category, extraction, risk, threats, unverified_org)

    # 7. plain-language summary (deterministic; AI summary appended when available and validated)
    top = list(dict.fromkeys(f.label for f in risk.top_factors))[:3]
    if top:
        summary = f"{risk.verdict_label}. Main concerns: " + "; ".join(top) + "."
    elif kind == "url":
        summary = ("Low-Risk Signals: nothing suspicious in the address itself. VERITAS did not open the page, and domain age or "
                   "reputation was not checked, so this says nothing about what the page contains.")
    else:
        summary = "Low-Risk Signals: no common scam indicators were found, but that does not prove the message is genuine."

    rid = uuid.uuid4().hex[:12]
    remember(rid, dict(text=norm, kind=kind, source_filename=source_filename, ocr_method=ocr_method,
                       ocr_note=ocr_note, raw_url=raw_url))
    ai_error = None
    if ai_err is not None:
        ai_error = str(ai_err) if isinstance(ai_err, ProviderError) else type(ai_err).__name__
    return AnalysisReport(
        id=rid,
        created_at=utcnow(),
        request_id=request_id,
        input=InputArtifact(kind=kind, source_filename=source_filename, sha256=sha256_hex(norm), char_count=len(norm),
                            preview=redact_preview(norm), ocr_method=ocr_method if kind == "image" else None, ocr_note=ocr_note),  # type: ignore[arg-type]
        category=category,
        category_label=actions.CATEGORY_LABELS[category],
        summary=summary,
        extraction=extraction,
        threat_signals=sorted(threats, key=lambda s: -s.weight),
        technical_signals=sorted(techs, key=lambda s: -s.weight),
        evidence=evidence,
        risk=risk,
        ai=AIReasoning(
            used=ai_out is not None, provider=provider.name if provider.available else "offline",
            summary=ai_summary, notes=ai_notes, configured=provider.available,
            assessment=ai_out.assessment if ai_out else None,
            observations=ai_out.key_observations if ai_out else [],
            suggested_checks=ai_out.suggested_checks if ai_out else [],
            error=ai_error, can_retry=provider.available and ai_out is None),
        action=plan,
        timeline=timeline,
        disclaimer=DISCLAIMER,
    )
