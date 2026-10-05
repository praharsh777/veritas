"""Bundled reference list of well-known organizations and their official domains.

IMPORTANT (evidence integrity): this is a *static list shipped with VERITAS*, not a live
lookup. Evidence derived from it is labelled "bundled reference" everywhere. Absence from
the list never implies fraud; presence of a mismatch is a reason to verify, not a verdict.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

REGISTRY_VERSION = "2026-10-03"

FREEMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "aol.com", "proton.me", "protonmail.com", "mail.com", "gmx.com", "icloud.com", "zoho.com",
}


@dataclass(frozen=True)
class Org:
    key: str
    name: str
    category: str  # bank | payments | retail | tech | carrier | government | social | crypto
    domains: tuple[str, ...]
    aliases: tuple[str, ...]
    verify_route: str  # how a person should independently reach this organization
    report_to: tuple[str, ...] = field(default_factory=tuple)


ORGS: tuple[Org, ...] = (
    Org("chase", "Chase", "bank", ("chase.com",), ("chase", "jpmorgan chase"),
        "Open the Chase app, or type chase.com yourself, or call the number printed on the back of your card."),
    Org("bofa", "Bank of America", "bank", ("bankofamerica.com",), ("bank of america", "bofa"),
        "Open the Bank of America app, or type bankofamerica.com yourself, or call the number on the back of your card."),
    Org("wellsfargo", "Wells Fargo", "bank", ("wellsfargo.com",), ("wells fargo",),
        "Open the Wells Fargo app, or type wellsfargo.com yourself, or call the number on the back of your card."),
    Org("citi", "Citi", "bank", ("citi.com", "citibank.com"), ("citibank", "citi"),
        "Open the Citi app, or type citi.com yourself, or call the number on the back of your card."),
    Org("capitalone", "Capital One", "bank", ("capitalone.com",), ("capital one",),
        "Open the Capital One app, or type capitalone.com yourself, or call the number on the back of your card."),
    Org("paypal", "PayPal", "payments", ("paypal.com",), ("paypal",),
        "Open the PayPal app or type paypal.com yourself and check the Notifications/Resolution Center there."),
    Org("amazon", "Amazon", "retail", ("amazon.com",), ("amazon",),
        "Open the Amazon app or type amazon.com yourself and check Your Orders / Message Center."),
    Org("microsoft", "Microsoft", "tech", ("microsoft.com", "live.com", "office.com", "microsoftonline.com"),
        ("microsoft", "windows support", "office 365", "microsoft 365"),
        "Type microsoft.com or account.microsoft.com yourself. Microsoft does not cold-call about computer problems."),
    Org("apple", "Apple", "tech", ("apple.com", "icloud.com"), ("apple", "icloud", "apple id", "apple support"),
        "Open Settings on your device or type apple.com yourself. Do not use phone numbers from pop-ups or messages."),
    Org("google", "Google", "tech", ("google.com",), ("google", "gmail"),
        "Type myaccount.google.com yourself and review Security > Recent activity."),
    Org("netflix", "Netflix", "retail", ("netflix.com",), ("netflix",),
        "Open the Netflix app or type netflix.com yourself and check Account."),
    Org("usps", "USPS", "carrier", ("usps.com",), ("USPS", "united states postal service", "postal service"),
        "Type usps.com yourself and enter the tracking number there.",
        ("USPS Postal Inspectors (uspis.gov)",)),
    Org("ups", "UPS", "carrier", ("ups.com",), ("UPS",),
        "Type ups.com yourself and enter the tracking number there."),
    Org("fedex", "FedEx", "carrier", ("fedex.com",), ("fedex",),
        "Type fedex.com yourself and enter the tracking number there."),
    Org("dhl", "DHL", "carrier", ("dhl.com",), ("DHL",),
        "Type dhl.com yourself and enter the tracking number there."),
    Org("irs", "IRS", "government", ("irs.gov",), ("IRS", "internal revenue service"),
        "Type irs.gov yourself. The IRS initiates contact by postal mail for most issues.",
        ("treasury.gov/tigta (TIGTA)", "reportfraud.ftc.gov")),
    Org("linkedin", "LinkedIn", "social", ("linkedin.com",), ("linkedin",),
        "Open the LinkedIn app or type linkedin.com yourself and check Messages/Notifications."),
    Org("meta", "Facebook / Instagram", "social", ("facebook.com", "instagram.com", "meta.com", "fb.com"),
        ("facebook", "instagram"),
        "Open the app or type facebook.com / instagram.com yourself and review Security and Login settings."),
    Org("coinbase", "Coinbase", "crypto", ("coinbase.com",), ("coinbase",),
        "Open the Coinbase app or type coinbase.com yourself. Coinbase will never ask you to move funds to a 'safe wallet'."),
)

ORG_BY_KEY = {o.key: o for o in ORGS}

# compile alias patterns: ALL-CAPS aliases are case-sensitive (IRS, UPS), others case-insensitive
_ALIAS_RES: list[tuple[Org, str, re.Pattern]] = []
for _o in ORGS:
    for _a in _o.aliases:
        flags = 0 if _a.isupper() else re.I
        _ALIAS_RES.append((_o, _a, re.compile(r"(?<![A-Za-z0-9])" + re.escape(_a) + r"(?![A-Za-z0-9])", flags)))


_EMAIL_OR_URL = re.compile(r"(?i)\b[\w.%+-]+@[\w.-]+\.\w+\b|\b(?:https?://|www\.)\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|io|co|top|xyz)\b\S*")


def find_orgs(text: str) -> list[tuple[Org, str]]:
    """Organizations mentioned in `text` (first alias hit per org).

    Email addresses, URLs and bare domains are blanked out first: 'gmail' inside
    'someone@gmail.com' is a mail provider, not the sender claiming to be Google.
    """
    text = _EMAIL_OR_URL.sub(lambda m: " " * len(m.group(0)), text)  # same length keeps positions stable
    seen: dict[str, tuple[Org, str]] = {}
    for org, alias, rx in _ALIAS_RES:
        m = rx.search(text)
        if m and org.key not in seen:
            seen[org.key] = (org, m.group(0))
    return list(seen.values())


def host_matches_official(host: str, org: Org) -> bool:
    host = host.lower().rstrip(".")
    return any(host == d or host.endswith("." + d) for d in org.domains)


def all_official_domains() -> dict[str, Org]:
    out: dict[str, Org] = {}
    for o in ORGS:
        for d in o.domains:
            out[d] = o
    return out
