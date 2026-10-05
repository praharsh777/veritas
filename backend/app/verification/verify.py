"""Evidence generation + claim cross-checking against the bundled reference list.

Never claims an organization "confirmed" anything. Outcomes are limited to
consistent / inconsistent with the bundled reference, or "Unable to independently verify".
"""
from __future__ import annotations

import re

from ..analysis.technical import host_of, registrable_domain
from ..schemas import Claim, Evidence, ExtractionResult, utcnow
from .registry import FREEMAIL_DOMAINS, ORG_BY_KEY, REGISTRY_VERSION, host_matches_official

LIMITS_BUNDLED = (
    f"Compared against a reference list bundled with VERITAS (snapshot {REGISTRY_VERSION}); this is not a live lookup "
    "and the list is not exhaustive. A mismatch is a reason to verify independently, not proof of fraud."
)


def cross_check(extraction: ExtractionResult) -> tuple[list[Evidence], bool, bool]:
    """Returns (evidence, org_resolved, unverified_org). Mutates claims in `extraction`."""
    evidence: list[Evidence] = []
    now = utcnow()
    eid = 0
    org_resolved = False
    org_entities = [e for e in extraction.entities if e.type == "organization" and e.registry_key and e.claimed]

    claim_by_entity = {c.entity: c for c in extraction.claims if c.entity}

    for ent in org_entities:
        org = ORG_BY_KEY[ent.registry_key]
        org_resolved = True
        claim = claim_by_entity.get(org.name)
        urls = [(u, host_of(u)) for u in extraction.urls]
        urls = [(u, h) for u, h in urls if h]
        emails = [e.name for e in extraction.entities if e.type == "email"]

        if not urls and not emails:
            eid += 1
            evidence.append(Evidence(
                id=f"e{eid}", kind="bundled_reference",
                title=f"Official domains for {org.name}",
                source_url=f"https://{org.domains[0]}", retrieved_at=now,
                supports=f"Message refers to {org.name}; no link or email address in it to compare.",
                outcome="informational",
                limitations=LIMITS_BUNDLED,
            ))
            if claim:
                claim.status = "unable_to_verify"
                claim.status_detail = (
                    f"Unable to independently verify that this came from {org.name}. Contact {org.name} through "
                    f"{org.domains[0]} (typed by you) or the app."
                )
                claim.evidence_ids.append(f"e{eid}")
            continue

        any_mismatch = False
        any_match = False
        for u, h in urls:
            eid += 1
            ok = host_matches_official(h, org)
            any_match |= ok
            any_mismatch |= not ok
            evidence.append(Evidence(
                id=f"e{eid}", kind="bundled_reference",
                title=f"Is '{registrable_domain(h)}' an official {org.name} domain?",
                source_url=f"https://{org.domains[0]}", retrieved_at=now,
                supports=f"Link in message → '{h}'; message refers to {org.name}.",
                outcome="consistent" if ok else "inconsistent",
                limitations=LIMITS_BUNDLED,
            ))
            if claim:
                claim.evidence_ids.append(f"e{eid}")
        for em in emails:
            dom = em.split("@")[-1].lower()
            eid += 1
            ok = host_matches_official(dom, org)
            any_match |= ok
            any_mismatch |= not ok
            note = " (free email provider)" if registrable_domain(dom) in FREEMAIL_DOMAINS else ""
            evidence.append(Evidence(
                id=f"e{eid}", kind="bundled_reference",
                title=f"Is '{dom}' an official {org.name} email domain?{note}",
                source_url=f"https://{org.domains[0]}", retrieved_at=now,
                supports=f"Contact address {em} in message; message refers to {org.name}.",
                outcome="consistent" if ok else "inconsistent",
                limitations=LIMITS_BUNDLED,
            ))
            if claim:
                claim.evidence_ids.append(f"e{eid}")
        if claim:
            if any_mismatch:
                claim.status = "inconsistent_with_reference"
                claim.status_detail = (
                    f"The message refers to {org.name}, but at least one link/contact does not match {org.name}'s "
                    f"official domains ({', '.join(org.domains)}) in the bundled reference."
                )
            elif any_match:
                claim.status = "consistent_with_reference"
                claim.status_detail = (
                    f"Links/contacts match {org.name}'s official domains in the bundled reference. This does not prove "
                    "the message is genuine (attackers can send real-looking messages that link to real sites)."
                )

    unverified_org = False
    # authority claims about organizations that are NOT in the bundled list
    for c in extraction.claims:
        if c.entity is None and c.verifiable:
            c.status = "unable_to_verify"
            if not c.status_detail:
                c.status_detail = ("Unable to independently verify. This organization is not in the bundled reference list; "
                                   "find its official website yourself and contact it through the details published there.")
    if not org_resolved and (extraction.authority_claims or extraction.claims):
        unverified_org = True
    for c in extraction.claims:
        if not c.verifiable and not c.status_detail:
            c.status = "unable_to_verify"
            c.status_detail = "Unable to independently verify this statement. Check it directly with the organization through an official channel."
    return evidence, org_resolved, unverified_org


async def live_checks(urls: list[str]) -> tuple[list[Evidence], list[str]]:
    """Optional: DNS + redirect-chain inspection with SSRF guards. Only runs when ENABLE_LIVE_URL_CHECKS=true.

    Returns (evidence, failures). Never raises; failures are reported honestly as 'unable to check'.
    """
    import httpx

    from ..config import settings
    from ..security.url_guard import UnsafeURL, assert_safe_to_fetch

    evidence: list[Evidence] = []
    failures: list[str] = []
    n = 100
    async with httpx.AsyncClient(timeout=settings.url_timeout_s, follow_redirects=False,
                                 headers={"User-Agent": "VERITAS-safety-check/1.0"}) as client:
        for raw in urls[:3]:
            url = raw if re.match(r"(?i)^https?://", raw) else "http://" + raw
            hops: list[str] = []
            try:
                for _ in range(4):
                    assert_safe_to_fetch(url, resolve=True)
                    r = await client.head(url)
                    hops.append(f"{r.status_code} {url}")
                    loc = r.headers.get("location")
                    if r.is_redirect and loc:
                        from urllib.parse import urljoin
                        url = urljoin(url, loc)
                        continue
                    break
                n += 1
                final_host = host_of(url) or ""
                evidence.append(Evidence(
                    id=f"e{n}", kind="live_check", title="Redirect chain (HEAD requests, no page content loaded)",
                    source_url=None, retrieved_at=utcnow(),
                    supports=f"Link '{raw[:80]}' → final host '{final_host}' after {len(hops)} request(s).",
                    outcome="informational",
                    limitations="Headers only; the destination page was not rendered or scanned. Reachability is not a reputation verdict.",
                    provenance="external_evidence",
                ))
            except UnsafeURL as e:
                failures.append(f"Live check skipped for a link: {e}.")
            except Exception:
                failures.append("Live check failed for a link (network error or timeout). Unable to check.")
    return evidence, failures
