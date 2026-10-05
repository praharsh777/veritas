"""Deterministic social-engineering / threat-signal rules.

Each rule is transparent: id, weight, regex, and a plain-language explanation.
Weights feed a combined score that is a communication aid, not a probability.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..schemas import ExtractionResult, ThreatSignal
from ..security.sanitize import detect_injection


@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    weight: float
    explanation: str
    patterns: tuple[str, ...]


RULES: tuple[Rule, ...] = (
    Rule("urgency", "Urgency / time pressure", 0.18,
         "Scammers create a short deadline so you act before you can check.",
         (r"\b(?:immediately|right now|asap|urgent(?:ly)?|act now|without delay|as soon as possible|hurry)\b",
          r"\bwithin (?:the next )?(?:\d+|an?|one|two|three|\w+) (?:minutes?|hours?)\b",
          r"\b(?:expires?|expiring|last chance|final (?:notice|warning)|today only|before midnight|limited time)\b",
          r"\b(?:will be|is being|gets?) (?:suspended|locked|closed|terminated|disabled|deactivated|cancelled|deleted)\b[^.\n]{0,40}\b(?:in|within|today|tonight|soon)\b")),
    Rule("fear_punishment", "Fear or punishment", 0.16,
         "Threats of loss, arrest, suspension or fees are used to override careful thinking.",
         (r"\b(?:suspend(?:ed)?|locked|blocked|frozen|freeze|terminated|disabled|deactivated|closed permanently|permanently (?:closed|disabled))\b",
          r"\b(?:arrest|warrant|lawsuit|legal action|prosecut\w+|police|jail|fine|penalt(?:y|ies)|deport\w*)\b",
          r"\b(?:unauthori[sz]ed|suspicious|fraudulent|unusual) (?:activity|access|login|sign[- ]?in|transaction|charge|attempt)\b",
          r"\b(?:compromised|hacked|breach(?:ed)?|virus|infected|malware)\b")),
    Rule("reward_lure", "Reward or lure", 0.15,
         "An unexpected prize, refund or unusually attractive offer is bait.",
         (r"\b(?:you(?:'ve| have)? (?:won|been selected|been chosen|qualify|are eligible)|congratulations)\b",
          r"\b(?:refund|reimbursement|cashback|bonus|prize|reward|lottery|inheritance|free (?:iphone|gift|money))\b",
          r"\b(?:work from home|no experience (?:needed|required)|earn \$?\d+[\d,]*\s?(?:/|per|a) ?(?:day|hour|week)|\$\d{2,3}[,\d]*\s?(?:per|/|a) (?:day|week|hour)|guaranteed (?:income|job|salary))\b",
          r"\b(?:selected for|offer letter|you(?:'re| are) hired|job offer|immediate(?:ly)? (?:start|joining))\b")),
    Rule("credential_otp_request", "Asks for a password, code, or secret", 0.42,
         "Real organizations do not ask you to disclose passwords, one-time codes or recovery phrases.",
         (r"\b(?:share|send|read(?: out)?|reply with|provide|tell|give|enter|confirm|verify)\b[^.\n]{0,45}\b(?:otp|one[- ]time (?:code|password|passcode)|verification code|security code|passcode|password|pin|recovery (?:code|phrase)|seed phrase|authentication code)\b",
          r"\b(?:otp|verification code|security code)\b[^.\n]{0,40}\b(?:share|send|read|tell|give|provide)\b",
          r"\b(?:reply|respond|text back|send back)\b[^.\n]{0,30}\b(?:\d[- ]?digit|verification|security|one[- ]time|confirmation) (?:code|number|pin)\b",
          r"\b(?:your|the) (?:password|pin|cvv|seed phrase|recovery phrase)\b[^.\n]{0,30}\b(?:is required|needed|to (?:verify|confirm|continue|proceed))\b")),
    Rule("advance_fee", "Asks you to pay a fee up front", 0.45,
         "Requests for a registration, processing, training, clearance or release fee before a job, prize or parcel are a hallmark of advance-fee fraud.",
         (r"\b(?:registration|application|processing|training|onboarding|clearance|redelivery|re-delivery|customs|release|handling|admin(?:istration)?|activation|verification|security) (?:fee|charge|cost|payment|deposit|kit)\b",
          r"\b(?:refundable|small|one[- ]time) (?:deposit|fee|payment|amount)\b",
          r"\b(?:pay|send|transfer|deposit)\b[^.\n]{0,40}\b(?:to (?:secure|confirm|reserve|activate|process|receive|release|unlock)|before (?:you|we) (?:start|can|begin|ship|release))\b",
          r"\bequipment (?:fee|deposit|kit|purchase)\b|\bpurchase (?:your |the )?(?:laptop|equipment|software|starter kit) (?:from|through) (?:our|a) (?:vendor|supplier)\b")),
    Rule("unconventional_payment", "Asks for gift cards, crypto, wire or peer-to-peer transfer", 0.45,
         "Gift cards, crypto, wire and instant-transfer apps are hard to reverse and favoured in fraud.",
         (r"\bgift ?cards?\b|\bitunes cards?\b|\bsteam cards?\b|\bgoogle play cards?\b",
          r"\b(?:bitcoin|btc|usdt|ethereum|crypto(?:currency)?|bitcoin atm)\b",
          r"\b(?:wire (?:transfer|the|funds|money)|western union|moneygram|zelle|cash ?app|venmo)\b")),
    Rule("payment_request", "Asks you to send money", 0.22,
         "A message that pushes you to pay should be verified through an independent channel first.",
         (r"\b(?:pay|send|transfer|remit|settle)\b[^.\n]{0,40}(?:\$\s?\d|\d[\d,.]*\s?(?:usd|dollars|inr|rupees|eur|gbp)|invoice|balance|outstanding|overdue)",
          r"\b(?:payment|invoice|balance|amount) (?:is )?(?:due|overdue|past due|outstanding|pending|required)\b")),
    Rule("payment_redirection", "Changed bank / payment details", 0.46,
         "A sudden change of bank account or payment instructions is the core of invoice and business-email-compromise fraud.",
         (r"\b(?:new|updated|changed|different|revised|temporary|alternate)\b[^.\n]{0,25}\b(?:bank|banking|account|routing|iban|swift|wire|payment|payee|beneficiary)\b[^.\n]{0,30}\b(?:details|information|number|instructions|account|info)\b",
          r"\b(?:we(?:'ve| have)? (?:changed|updated|switched|moved)|has changed|have changed)\b[^.\n]{0,40}\b(?:bank|account|payment)\b",
          r"\b(?:please|kindly)\b[^.\n]{0,30}\b(?:remit|send|pay|transfer)\b[^.\n]{0,40}\b(?:to the (?:new|following|below|attached)|new account)\b")),
    Rule("remote_access_request", "Asks for remote access to your device", 0.46,
         "Remote-access tools let a stranger see and control your device and accounts.",
         (r"\b(?:anydesk|teamviewer|quicksupport|ultraviewer|logmein|splashtop|rustdesk)\b",
          r"\bremote (?:access|desktop|session|support|control|assistance)\b",
          r"\b(?:let us|allow us to|give us|grant us)\b[^.\n]{0,30}\b(?:access|control)\b[^.\n]{0,20}\b(?:computer|device|pc|laptop|phone)\b")),
    Rule("secrecy_isolation", "Asks you to keep it secret", 0.2,
         "Isolation stops friends, family or your bank from spotting the scam.",
         (r"\b(?:do not|don't|dont|never)\b[^.\n]{0,20}\b(?:tell|share|discuss|inform|mention|speak|talk)\b[^.\n]{0,25}\b(?:anyone|anybody|family|friends|bank|manager|colleagues?|others|staff|branch)\b",
          r"\bkeep (?:this|it) (?:confidential|secret|private|between us|quiet)\b",
          r"\b(?:confidential|secret) (?:matter|transaction|assignment|operation)\b")),
    Rule("authority_impersonation", "Claims to be an authority or known organization", 0.12,
         "Impersonating a bank, employer, carrier or agency borrows trust you did not extend.",
         (r"\b(?:this is|we are|i am|i'm|calling from|message from|notice from|alert from|on behalf of|official (?:notice|message|alert)|representative (?:of|from)|agent (?:from|at|with)|from the)\b[^.\n]{0,60}\b(?:bank|security|fraud (?:department|team|prevention)|support|department|compliance|billing|accounts? team|government|agency|officer|irs|usps|fedex|ups|dhl|microsoft|apple|amazon|paypal|recruit(?:er|ment|ing)|hr|human resources|hiring (?:team|manager))\b",)),
    Rule("ai_impersonation_pattern", "Pattern consistent with AI/voice/video impersonation of a known person", 0.28,
         "Messages that claim to be a relative or executive using a new number or a voice/video call, with urgency and money, match known deepfake and impersonation scams. VERITAS does not analyse audio or video itself.",
         (r"\b(?:new (?:phone )?number|lost my phone|phone (?:broke|is broken|died)|changed (?:my )?number)\b[^.\n]{0,60}",
          r"\b(?:it'?s me|this is your (?:son|daughter|boss|ceo|manager|brother|sister|friend))\b",
          r"\b(?:voice|video) (?:message|call|clip|note)\b[^.\n]{0,80}\b(?:urgent|money|transfer|pay|help|emergency|cash)\b",
          r"\b(?:i(?:'m| am) in (?:trouble|an emergency|jail|hospital)|need (?:money|cash|help) (?:right now|urgently|asap|today))\b")),
    Rule("unusual_contact_channel", "Moves the conversation to an unusual channel", 0.15,
         "Unsolicited requests to continue on WhatsApp/Telegram or via a personal address bypass an organization's official channels.",
         (r"\b(?:contact|message|text|add|reach|chat|ping|dm)\b[^.\n]{0,40}\b(?:whatsapp|telegram|signal|wechat|skype|hangouts)\b",
          r"\b(?:whatsapp|telegram|wechat)\b[^.\n]{0,30}\b(?:\+?\d[\d\s().-]{7,}|number|@\w+)\b",
          r"\b(?:interview|onboarding|chat) (?:will be|is|via|on|through) (?:conducted )?(?:via|on|through|over) (?:telegram|whatsapp|text|google chat|hangouts)\b")),
    Rule("unsolicited_lowskill_work", "Unsolicited offer of low-skill remote work", 0.22,
         "Data entry, document typing and 'virtual assistant' work offered out of the blue is a very common recruitment-scam opener; real employers rarely cold-contact for these roles.",
         (r"\b(?:data entry|document typing|typing (?:jobs?|work|projects?)|virtual assistan(?:t|ce)|form filling|copy[- ]?paste (?:jobs?|work)|captcha (?:jobs?|work)|online (?:survey|rating|review) (?:jobs?|tasks?)|product (?:rating|review) tasks?)\b",)),
    Rule("provider_spam_warning", "Your mail provider flagged similar messages as spam", 0.2,
         "The email service itself warned about this sender or message. That warning is part of the screenshot and is worth taking seriously.",
         (r"\b(?:similar to|like) messages that were identified as spam\b",
          r"\bwhy is this message in spam\b|\bwhy is th\w* message in spam\b|\bidentified as spam in the past\b",
          r"\b(?:this message|sender) (?:may be|might be|is) (?:dangerous|suspicious|unsafe)\b|\bbe careful with this (?:message|sender)\b|\bthis (?:message|sender) failed (?:spf|dkim|dmarc|authentication)\b",
          r"\bmarked as (?:spam|phishing)\b")),
    Rule("bulk_recipients", "Sent to many recipients at once", 0.15,
         "The message was addressed to a long list of people. Genuine individual hiring, banking or support messages are rarely sent as one mass mailing with everyone visible.",
         (r"(?im)^[^\n]{0,12}\bto\b[^\n,]{1,40}(?:,[^\n,]{1,40}){5,}",)),
    Rule("generic_greeting", "Generic greeting instead of your name", 0.08,
         "Messages that really concern you usually use your name. 'Dear Applicant/Customer' is typical of mass-sent messages.",
         (r"(?im)^\s*dear\s+(?:applicant|candidate|customer|user|member|sir\s*/\s*madam|sir or madam|valued customer|account holder|beneficiary|friend|student)\b",)),
    Rule("external_form_collection", "Collects details through a generic online form", 0.12,
         "Asking you to hand over personal details via a free form-builder link (instead of the organization's own website) is common in mass recruitment and survey scams. Form-builders are legitimate tools, so this is only a mild signal.",
         (r"https?://(?:docs\.google\.com/forms|forms\.gle|forms\.office\.com|[\w-]+\.typeform\.com|(?:www\.)?jotform\.com|[\w.-]*surveymonkey\.com)\S*",
          r"\b(?:docs\.google\.com/forms|forms\.gle)/\S+")),
    Rule("conversation_context_manipulation", "Fabricated prior relationship or context", 0.15,
         "Claims like 'as we discussed' or 'per our call' invent history to lower your guard.",
         (r"\b(?:as (?:we|i) (?:discussed|agreed|spoke)|per our (?:call|conversation|discussion)|following up on our (?:call|conversation)|as promised)\b",
          r"\b(?:you (?:applied|signed up|registered|subscribed|ordered|requested)) (?:for|to|on)\b[^.\n]{0,40}\b(?:recently|yesterday|last week|earlier)\b")),
)
_COMPILED = [(r, [re.compile(p, re.I) for p in r.patterns]) for r in RULES]


def _excerpt(text: str, m: re.Match, pad: int = 18) -> str:
    s, e = max(0, m.start() - pad), min(len(text), m.end() + pad)
    return text[s:e].replace("\n", " ").strip()[:160]


def detect_threat_signals(text: str, extraction: ExtractionResult | None = None) -> list[ThreatSignal]:
    out: list[ThreatSignal] = []
    for rule, rxs in _COMPILED:
        excerpts: list[str] = []
        for rx in rxs:
            m = rx.search(text)
            if m:
                ex = _excerpt(text, m)
                if ex not in excerpts:
                    excerpts.append(ex)
            if len(excerpts) >= 3:
                break
        if excerpts:
            out.append(
                ThreatSignal(
                    id=rule.id,
                    label=rule.label,
                    weight=rule.weight,
                    explanation=rule.explanation,
                    excerpts=excerpts,
                    provenance="observed_input" if rule.id in {"urgency", "fear_punishment", "reward_lure", "provider_spam_warning"} else "deterministic_rule",
                )
            )
    # derived: the message invokes a known organization AND pairs it with pressure or a sensitive request
    if extraction is not None and not any(s.id == "authority_impersonation" for s in out):
        head = text[:70].lower()
        orgs = [e.name for e in extraction.entities
                if e.type == "organization" and any(a in head for a in (e.name.lower(), e.name.lower().split(" /")[0]))]
        pressure = {"urgency", "fear_punishment", "credential_otp_request", "advance_fee", "payment_request", "reward_lure"}
        if orgs and any(s.id in pressure for s in out):
            rule = next(r for r in RULES if r.id == "authority_impersonation")
            out.append(ThreatSignal(
                id=rule.id, label=rule.label, weight=rule.weight,
                explanation=f"The message invokes {orgs[0]} while pressuring or asking something of you. " + rule.explanation,
                excerpts=[f"References {orgs[0]}"], provenance="deterministic_rule"))
    inj = detect_injection(text)
    if inj:
        out.append(
            ThreatSignal(
                id="prompt_injection_attempt",
                label="Message tries to instruct an AI system",
                weight=0.3,
                explanation="The content contains text addressed to an AI/assistant (e.g. 'ignore previous instructions'). "
                "VERITAS treated it purely as data and did not follow it. Legitimate messages do not do this.",
                excerpts=inj[:3],
                provenance="deterministic_rule",
            )
        )
    return out
