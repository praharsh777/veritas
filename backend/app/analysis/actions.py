"""Scenario classification and the 'Verify Before You Act' plan.

Verification routes always point the USER to a destination they type or open themselves
(or to a channel they already trust) — never to a link inside the suspicious message.
"""
from __future__ import annotations

from ..schemas import (
    ActionRecommendation,
    Category,
    ExtractionResult,
    RiskAssessment,
    ThreatSignal,
    VerificationStep,
)
from ..verification.registry import ORG_BY_KEY

CATEGORY_LABELS: dict[str, str] = {
    "bank_account_alert": "Account alert / bank impersonation",
    "job_offer": "Job offer / recruitment",
    "tech_support": "Customer or tech support request",
    "invoice_payment": "Invoice / payment-detail change",
    "delivery": "Delivery / parcel notice",
    "impersonation": "Person or executive impersonation",
    "prize_lure": "Prize / refund / reward lure",
    "unclassified": "General message",
}

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "bank_account_alert": ("account", "suspend", "locked", "verify", "bank", "card", "login", "sign-in", "unusual activity", "security alert", "debit", "credit"),
    "job_offer": ("data entry", "virtual assistan", "document typing", "collaborate with us", "job", "position", "hiring", "recruit", "salary", "interview", "offer letter", "work from home", "onboarding", "employer", "candidate", "role"),
    "tech_support": ("support", "technician", "remote", "anydesk", "teamviewer", "virus", "infected", "your computer", "refund department", "otp", "verification code", "security code", "customer care"),
    "invoice_payment": ("invoice", "wire", "remittance", "beneficiary", "vendor", "purchase order", "payment instructions", "bank details", "routing", "iban", "accounts payable"),
    "delivery": ("package", "parcel", "delivery", "shipment", "tracking", "redelivery", "courier", "customs", "address"),
    "impersonation": ("new number", "it's me", "this is your", "lost my phone", "video call", "voice message", "gift card", "need help", "emergency", "ceo", "boss"),
    "prize_lure": ("won", "prize", "lottery", "refund", "congratulations", "reward", "claim", "cashback", "inheritance"),
}


def classify(text: str, signals: list[ThreatSignal]) -> Category:
    t = text.lower()
    scores = {c: sum(1 for k in kws if k in t) for c, kws in _KEYWORDS.items()}
    ids = {s.id for s in signals}
    if "payment_redirection" in ids:
        scores["invoice_payment"] += 4
    if "remote_access_request" in ids:
        scores["tech_support"] += 3
    if "advance_fee" in ids and scores["job_offer"] >= 1:
        scores["job_offer"] += 3
    if "ai_impersonation_pattern" in ids:
        scores["impersonation"] += 3
    if "credential_otp_request" in ids:
        scores["bank_account_alert"] += 1
        scores["tech_support"] += 1
    best = max(scores.items(), key=lambda kv: kv[1])
    return best[0] if best[1] >= 2 else "unclassified"  # type: ignore[return-value]


_GENERIC_REPORT = ["reportfraud.ftc.gov (US)", "Your local consumer-protection or cybercrime reporting service"]


def build_action_plan(
    category: Category,
    extraction: ExtractionResult,
    risk: RiskAssessment,
    signals: list[ThreatSignal],
    unverified_org: bool,
) -> ActionRecommendation:
    orgs = [ORG_BY_KEY[e.registry_key] for e in extraction.entities if e.registry_key and e.claimed]
    org = orgs[0] if orgs else None
    sig = {s.id for s in signals}
    steps: list[VerificationStep] = []
    do_now: list[str] = []
    do_not: list[str] = [
        "Do not click links, open attachments, or call numbers that appear in this message.",
    ]
    report_to = list(_GENERIC_REPORT)

    if org:
        steps.append(VerificationStep(
            order=1,
            title=f"Go to {org.name} yourself",
            detail=org.verify_route,
            route=org.domains[0],
        ))
        report_to = list(org.report_to) + report_to
    elif category in ("job_offer", "delivery", "invoice_payment", "tech_support", "bank_account_alert", "impersonation") and unverified_org:
        steps.append(VerificationStep(
            order=1,
            title="Unable to independently verify the sender",
            detail="VERITAS could not match the sender to an official source. Look the organization up yourself using a search "
                   "engine or a number you already trust, and compare what you find with this message.",
            status="unable_to_verify",
        ))

    if category == "bank_account_alert":
        do_now += ["Open your bank's app or type its address yourself and check for alerts.",
                   "If you already entered details on the linked page, change that password now and call your bank."]
        do_not += ["Do not share one-time codes, PINs or passwords with anyone who contacts you first."]
        steps.append(VerificationStep(order=len(steps) + 1, title="Call the number on your card",
                    detail="Use the phone number printed on the back of your card or on your statement, not one from this message."))
    elif category == "job_offer":
        do_now += ["Find the company's official careers page by searching for it yourself and see whether this role is listed.",
                   "Check that the recruiter's email domain matches the company's real domain."]
        do_not += ["Do not pay any fee, deposit, or 'equipment' cost to get a job.",
                   "Do not send ID documents, bank details or a photo of your ID before a verified offer."]
        steps.append(VerificationStep(order=len(steps) + 1, title="Confirm the role on the employer's own site",
                    detail="Search for the employer, open its official careers page from your own search, and contact HR through the details published there."))
    elif category == "tech_support":
        do_now += ["End the call/chat. If you installed anything or gave access, disconnect from the internet and uninstall it.",
                   "Change passwords for important accounts from a different, clean device."]
        do_not += ["Do not install remote-access software or give anyone control of your device.",
                   "Do not read out codes sent to your phone or email."]
        steps.append(VerificationStep(order=len(steps) + 1, title="Contact support through the official app or site",
                    detail="Open the company's own app or type its address yourself and use the support option there."))
    elif category == "invoice_payment":
        do_now += ["Pause the payment. Call the vendor/colleague on a number already saved in your records.",
                   "Ask your finance/IT team to check the sender address and headers."]
        do_not += ["Do not change payee bank details because of an email request alone."]
        steps.append(VerificationStep(order=len(steps) + 1, title="Call back on a previously trusted number",
                    detail="Confirm the new payment details by phone using contact information you already had before this message arrived."))
    elif category == "delivery":
        do_now += ["Check your own order emails/app for a real tracking number."]
        do_not += ["Do not pay a 'redelivery' or 'customs' fee through a link in a text."]
        steps.append(VerificationStep(order=len(steps) + 1, title="Track the parcel on the carrier's site",
                    detail="Type the carrier's address yourself and paste the tracking number from your original order confirmation."))
    elif category == "impersonation":
        do_now += ["Contact the person on a number you already have, or through another channel, before doing anything.",
                   "Ask a question only the real person would know."]
        do_not += ["Do not send money, gift cards or codes because of a message, voice note or video call alone."]
        steps.append(VerificationStep(order=len(steps) + 1, title="Call the person back on a saved number",
                    detail="Voices and faces can be faked. A separate, trusted channel is the safest check."))
    elif category == "prize_lure":
        do_now += ["Treat unexpected prizes and refunds as unverified until you confirm with the organization directly."]
        do_not += ["Do not pay anything to 'release' a prize or refund."]
    else:
        do_now += ["If the message asks you to do something with money, accounts or personal data, verify it through a channel you already trust."]

    if "credential_otp_request" in sig:
        do_not.append("Never give out one-time codes, passwords, PINs or recovery phrases.")
    if "unconventional_payment" in sig or "advance_fee" in sig:
        do_not.append("Do not pay with gift cards, crypto, wire transfer or payment apps in response to this message.")
    if "remote_access_request" in sig:
        do_not.append("Do not allow remote access to your computer or phone.")

    steps = [VerificationStep(order=i + 1, title=s.title, detail=s.detail, route=s.route, status=s.status)
             for i, s in enumerate(steps)]

    if risk.risk_level == "high_risk":
        headline = "Do not act on this message yet. Verify through an independent channel first."
    elif risk.risk_level == "needs_verification":
        headline = "Verify before you act. Some details do not add up or cannot be confirmed."
    else:
        headline = "No strong warning signs found, but this is not a guarantee. Verify anything involving money or personal data."
    return ActionRecommendation(headline=headline, do_now=do_now, do_not=list(dict.fromkeys(do_not)),
                                verification_steps=steps, report_to=report_to[:4])
