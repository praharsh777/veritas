"""Deterministic structured extraction: entities, URLs, requests, deadlines, payments, contacts."""
from __future__ import annotations

import re

from ..schemas import (
    Claim,
    ExtractedEntity,
    ExtractionResult,
    RequestedAction,
    RequestedData,
)
from ..verification.registry import find_orgs

_TLDS = (
    "com|net|org|info|biz|co|io|gov|edu|us|uk|in|ca|de|app|dev|online|site|shop|store|support|help|top|xyz|"
    "click|link|work|loan|icu|vip|live|club|cyou|buzz|cfd|sbs|rest|zip|mov|tk|ml|ga|cf|gq|ru|cn"
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"'\])]+")
_BARE_DOMAIN_RE = re.compile(
    r"(?i)(?<![@\w.-])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:" + _TLDS + r"))(?![\w-])(/[^\s<>\"'\])]*)?"
)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
_MONEY_RE = re.compile(
    r"(?:[$€£₹]\s?\d[\d,]*(?:\.\d{1,2})?)|(?:\b\d[\d,]*(?:\.\d{1,2})?\s?(?:USD|usd|dollars|INR|rupees|EUR|GBP)\b)"
)
_DEADLINE_RES = [
    re.compile(r"(?i)\bwithin (?:the next )?(?:\d+|an?|one|two|three|four|five|six|twelve|twenty[- ]four|forty[- ]eight) (?:minutes?|hours?|days?)\b"),
    re.compile(r"(?i)\b(?:in|after) (?:the next )?\d+ (?:minutes?|hours?)\b"),
    re.compile(r"(?i)\b(?:immediately|right now|asap|urgent(?:ly)?|today only|by (?:end of day|midnight|tomorrow|tonight))\b"),
    re.compile(r"(?i)\b(?:final|last) (?:notice|warning|chance|reminder)\b"),
]

_ACTION_RULES: list[tuple[str, str, str]] = [
    ("click_link", "Click / open a link", r"\b(?:click|tap|open|follow|visit|go to|log ?in (?:at|via|through))\b[^.\n]{0,50}\b(?:link|url|here|below|website|site|portal|http|www)"),
    ("verify_account", "Verify / confirm / update account details", r"\b(?:verify|confirm|validate|re-?activate|restore|unlock|update)\b[^.\n]{0,30}\b(?:account|identity|information|details|profile|payment|billing|card|login|access)\b"),
    ("call_number", "Call a phone number from the message", r"\b(?:call|dial|phone|contact)\b[^.\n]{0,40}(?:\+?\d[\d\s().-]{8,}|number|hotline|helpline|support line)"),
    ("pay_fee", "Pay a fee / deposit", r"\b(?:pay|send|transfer|deposit|remit|submit)\b[^.\n]{0,40}\b(?:fee|deposit|charge|payment|amount|balance|invoice|kit|\$\s?\d)"),
    ("gift_cards", "Buy gift cards", r"\bgift ?cards?\b|\bitunes cards?\b|\bsteam cards?\b"),
    ("install_software", "Install software / allow remote control", r"\b(?:install|download|run|open)\b[^.\n]{0,40}\b(?:anydesk|teamviewer|quicksupport|ultraviewer|remote (?:access|desktop|support)|apk|\.exe|software|app)\b"),
    ("share_code", "Share a code / password", r"\b(?:share|send|read(?: out)?|reply with|provide|tell|give|enter|confirm)\b[^.\n]{0,40}\b(?:code|otp|one[- ]time|passcode|pin|password|passcode)\b"),
    ("move_conversation", "Move to another channel", r"\b(?:message|contact|text|add|reach|chat|ping)\b[^.\n]{0,30}\b(?:whatsapp|telegram|signal|wechat|hangouts|skype)\b"),
    ("open_attachment", "Open an attachment", r"\b(?:open|view|see|download|review)\b[^.\n]{0,25}\b(?:attached|attachment|pdf|document|invoice|statement)\b"),
    ("change_payment_details", "Use new / changed payment details", r"\b(?:new|updated|changed|different|revised)\b[^.\n]{0,25}\b(?:bank|account|routing|iban|wire|payment|payee|beneficiary)\b[^.\n]{0,25}\b(?:details|information|number|instructions|account)?"),
    ("keep_secret", "Keep it confidential", r"\b(?:do not|don't|dont|never)\b[^.\n]{0,20}\b(?:tell|share|discuss|inform|mention)\b[^.\n]{0,25}\b(?:anyone|anybody|family|bank|manager|colleagues?|others)\b|\bkeep (?:this|it) (?:confidential|secret|private|between us)\b"),
    ("wire_or_crypto", "Wire / crypto transfer", r"\b(?:wire|bitcoin|btc|usdt|crypto(?:currency)?|zelle|cash ?app|western union|moneygram)\b"),
]
_ACTION_RES = [(a, l, re.compile(p, re.I)) for a, l, p in _ACTION_RULES]

_DATA_RULES: list[tuple[str, str, str]] = [
    ("password", "Password / login credentials", r"\b(?:password|passcode|login (?:details|credentials)|username and password|credentials)\b"),
    ("otp", "One-time code / verification code", r"\b(?:otp|one[- ]time (?:code|password|passcode)|verification code|security code|6[- ]digit code|authentication code|2fa code)\b"),
    ("recovery", "Recovery phrase / backup code", r"\b(?:recovery (?:code|phrase)|seed phrase|backup codes?|secret recovery)\b"),
    ("ssn", "Social Security / national ID number", r"\b(?:social security|ssn|national id|aadhaar|passport number|driver'?s licen[cs]e)\b"),
    ("card", "Card number / CVV / PIN", r"\b(?:card number|credit card|debit card|cvv|cvc|card details|atm pin|\bpin\b)\b"),
    ("bank_details", "Bank account / routing details", r"\b(?:bank (?:account|details|login)|routing number|account number|iban|net ?banking)\b"),
    ("identity_docs", "Identity documents / photo ID", r"\b(?:copy of (?:your )?(?:id|passport)|photo id|selfie with|scan of (?:your )?(?:id|passport))\b"),
    ("dob", "Date of birth", r"\b(?:date of birth|dob|birth ?date)\b"),
]
_DATA_RES = [(a, l, re.compile(p, re.I)) for a, l, p in _DATA_RULES]

_PAYMENT_RE = re.compile(
    r"(?i)\b(?:pay|send|transfer|deposit|remit|buy|purchase)\b[^.\n]{0,60}(?:\$\s?\d[\d,.]*|\d[\d,.]*\s?(?:usd|dollars|inr|rupees)|fee|deposit|gift ?cards?|bitcoin|crypto|wire)"
    r"|\b(?:registration|processing|training|onboarding|clearance|redelivery|customs|release|handling|admin(?:istration)?) (?:fee|charge|cost|payment|deposit|kit)\b"
)
_AUTHORITY_RE = re.compile(
    r"(?i)\b(?:this is|we are|i am|i'm|calling from|message from|notice from|on behalf of|official|representative of|agent (?:from|at|with))\b[^.\n]{0,60}\b(?:bank|security|fraud|support|department|team|desk|service|recruiter|hr|human resources|hiring|compliance|billing|accounts?|government|agency|officer|manager|ceo|director)\b"
)
_CHANNEL_RES = [
    ("whatsapp", re.compile(r"(?i)\bwhats ?app\b")),
    ("telegram", re.compile(r"(?i)\btelegram\b")),
    ("signal", re.compile(r"(?i)\bsignal (?:app|me|group)\b")),
    ("sms/text", re.compile(r"(?i)\b(?:text me|sms|text message)\b")),
    ("wechat", re.compile(r"(?i)\bwechat\b")),
]


_UNKNOWN_ORG_RE = re.compile(
    r"\b(?:on behalf of|representing|recruiter (?:at|with|from)|recruiting for|hiring for|working (?:with|for|at)|team at|"
    r"employed (?:by|at)|agent (?:of|for|at)|"
    r"(?:opportunity|internship|position|role|job|vacancy|opening|offer|career|employment|program(?:me)?) (?:at|with))\s+"
    r"((?:[A-Z][\w&.'-]*)(?:\s+(?:&|and|of|[A-Z][\w&.'-]*)){0,4})"
)


def _snip(text: str, m: re.Match, pad: int = 20) -> str:
    s = max(0, m.start() - pad)
    e = min(len(text), m.end() + pad)
    return text[s:e].replace("\n", " ").strip()


def clean_url(u: str) -> str:
    return u.rstrip(".,;:!?)\"'")


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    no_email = _EMAIL_RE.sub(" ", text)
    for m in _URL_RE.finditer(no_email):
        urls.append(clean_url(m.group(0)))
    covered = " ".join(urls).lower()
    for m in _BARE_DOMAIN_RE.finditer(no_email):
        cand = clean_url(m.group(1) + (m.group(2) or ""))
        if cand.lower() not in covered and m.group(1).lower() not in covered:
            urls.append(cand)
    seen, out = set(), []
    for u in urls:
        k = u.lower()
        if k not in seen:
            seen.add(k)
            out.append(u)
    return out[:15]


_CLAIM_CUES = re.compile(
    r"(?i)(?:\bthis is\b|\bwe are\b|\bi am\b|\bi'm\b|\bon behalf of\b|\bofficial\b|\bmessage from\b|\bnotice from\b|\balert from\b|"
    r"\bcalling from\b|\bteam at\b|\brepresentative\b|\bsecurity (?:team|department)\b|\bfrom:)[^.\n]{0,30}$"
)


def org_is_claimed(text: str, alias: str) -> bool:
    """True when the message presents itself as coming from the org (sender/header position or
    'this is X' style cue). A passing mention ('I found you on LinkedIn') is NOT a claim."""
    from ..verification.registry import _EMAIL_OR_URL
    text = _EMAIL_OR_URL.sub(lambda m: " " * len(m.group(0)), text)
    m = re.search(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])", text, 0 if alias.isupper() else re.I)
    if not m:
        return False
    if m.start() < 60:
        return True
    return bool(_CLAIM_CUES.search(text[max(0, m.start() - 45): m.start()]))


def extract(text: str, injected_urls: list[str] | None = None) -> ExtractionResult:
    res = ExtractionResult()
    res.urls = extract_urls(text)
    for u in injected_urls or []:
        if u not in res.urls:
            res.urls.insert(0, u)

    # organizations
    for org, alias in find_orgs(text):
        res.entities.append(
            ExtractedEntity(name=org.name, type="organization", registry_key=org.key, provenance="observed_input",
                            claimed=org_is_claimed(text, alias))
        )

    emails = sorted({m.group(0) for m in _EMAIL_RE.finditer(text)})
    for e in emails:
        res.entities.append(ExtractedEntity(name=e, type="email"))
    phones = []
    for m in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) >= 10 and m.group(0).strip() not in phones:
            phones.append(m.group(0).strip())
    for p in phones[:5]:
        res.entities.append(ExtractedEntity(name=p, type="phone"))
    for m in _MONEY_RE.finditer(text):
        res.entities.append(ExtractedEntity(name=m.group(0).strip(), type="money"))

    res.contact_channels = [*emails, *phones[:5], *[n for n, rx in _CHANNEL_RES if rx.search(text)]]

    for rx in _DEADLINE_RES:
        for m in rx.finditer(text):
            d = m.group(0).strip()
            if d.lower() not in [x.lower() for x in res.deadlines]:
                res.deadlines.append(d)

    for action, label, rx in _ACTION_RES:
        m = rx.search(text)
        if m:
            res.requested_actions.append(RequestedAction(action=action, label=label, excerpt=_snip(text, m)))

    for dtype, label, rx in _DATA_RES:
        m = rx.search(text)
        if m:
            res.requested_data.append(RequestedData(data_type=dtype, label=label, excerpt=_snip(text, m)))

    for m in _PAYMENT_RE.finditer(text):
        s = _snip(text, m, 10)
        if s not in res.payment_requests:
            res.payment_requests.append(s)
    res.payment_requests = res.payment_requests[:5]

    for m in _AUTHORITY_RE.finditer(text):
        s = _snip(text, m, 0)
        if s not in res.authority_claims:
            res.authority_claims.append(s)
    res.authority_claims = res.authority_claims[:4]

    # organizations the sender says they represent that are NOT in the bundled reference
    known = {e.name.lower() for e in res.entities if e.type == "organization"}
    for m in _UNKNOWN_ORG_RE.finditer(text):
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        cut = re.search(r"\b(?:Ltd|Limited|Inc|LLC|LLP|Corp|Corporation|GmbH|Company|Group|Co|Bank)\b\.?", name)
        if cut:
            name = name[: cut.end()]  # stop at the company-type suffix ("... Ltd." not "... Ltd. We")
        else:
            name = re.split(r"(?<=[a-z])\.\s", name)[0]  # stop at end of sentence
        name = name.strip(" ,'")
        if len(name) < 3 or name.lower() in known or any(name.lower() in k or k in name.lower() for k in known):
            continue
        known.add(name.lower())
        res.entities.append(ExtractedEntity(name=name, type="organization", registry_key=None, claimed=True,
                                            provenance="observed_input"))
        if name not in res.authority_claims:
            res.authority_claims.append(f"Says it represents {name}")

    # claims (checkable assertions the message makes)
    n = 0
    for e in res.entities:
        if e.type == "organization" and e.registry_key is None and e.claimed:
            n += 1
            res.claims.append(Claim(id=f"c{n}", text=f"The sender says they represent {e.name.rstrip('.')}.", entity=None,
                                    verifiable=True, provenance="observed_input"))
    for org, alias in find_orgs(text):
        if not org_is_claimed(text, alias):
            continue  # a passing mention is not an identity claim
        n += 1
        res.claims.append(
            Claim(
                id=f"c{n}",
                text=f"The message presents itself as, or refers to, {org.name}.",
                entity=org.name,
                verifiable=True,
                provenance="observed_input",
            )
        )
    for m in re.finditer(
        r"(?i)\b(?:your account (?:has been|will be|is|was) [^.\n]{3,60}|(?:unusual|suspicious|unauthori[sz]ed) (?:activity|login|sign[- ]?in|transaction)[^.\n]{0,50}|package[^.\n]{0,40}(?:could not|couldn't|cannot|unable|held|on hold)[^.\n]{0,30}|you (?:have been|are|were) (?:selected|hired|approved|chosen)[^.\n]{0,40}|you (?:won|have won)[^.\n]{0,40}|payment (?:is )?(?:overdue|past due|failed|declined)[^.\n]{0,30})",
        text,
    ):
        n += 1
        res.claims.append(
            Claim(id=f"c{n}", text=_snip(text, m, 0)[:160], verifiable=False, provenance="observed_input")
        )
        if n >= 8:
            break
    return res
