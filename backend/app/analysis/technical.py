"""Deterministic URL / domain / email technical signals. No network access in this module."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ..schemas import TechnicalSignal
from ..security.url_guard import literal_ip
from ..verification.registry import FREEMAIL_DOMAINS, ORGS, Org, all_official_domains, host_matches_official

MULTI_PART_SUFFIXES = {
    "co.uk", "org.uk", "gov.uk", "ac.uk", "com.au", "net.au", "co.in", "co.jp", "com.br", "co.nz", "com.mx",
    "co.za", "com.sg", "com.cn", "com.tr", "com.ng",
}
SUSPICIOUS_TLDS = {
    "top", "xyz", "click", "link", "work", "loan", "icu", "vip", "cyou", "buzz", "cfd", "sbs", "rest", "zip",
    "mov", "tk", "ml", "ga", "cf", "gq", "support", "help", "monster", "country", "kim", "men", "date",
}
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "cutt.ly", "rb.gy", "shorturl.at", "tiny.cc",
    "buff.ly", "rebrand.ly",
}
BAIT_WORDS = {
    "secure", "verify", "verification", "login", "signin", "account", "update", "support", "alert", "billing",
    "confirm", "unlock", "recover", "helpdesk", "service", "customer", "refund", "claim", "redelivery",
    "tracking", "payment", "wallet", "safe",
}
_CONFUSABLE = [("rn", "m"), ("vv", "w"), ("cl", "d")]
_DIGIT_MAP = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b"})


def host_of(url: str) -> str | None:
    u = url if re.match(r"(?i)^[a-z][a-z0-9+.-]*://", url) else "http://" + url
    try:
        h = urlsplit(u).hostname
    except ValueError:
        return None
    return h.lower().rstrip(".") if h else None


def registrable_domain(host: str) -> str:
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    last2 = ".".join(parts[-2:])
    if last2 in MULTI_PART_SUFFIXES and len(parts) >= 3:
        return ".".join(parts[-3:])
    return last2


def _label(domain: str) -> str:
    return domain.split(".")[0]


def _lev(a: str, b: str, cap: int = 3) -> int:
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _normalize_confusables(s: str) -> str:
    s = s.translate(_DIGIT_MAP)
    for a, b in _CONFUSABLE:
        s = s.replace(a, b)
    return s


def lookalike_of(domain: str) -> tuple[str, str] | None:
    """If `domain` imitates a known official domain without being it, return (official_domain, org_name)."""
    official = all_official_domains()
    if domain in official:
        return None
    label = _label(domain)
    nl = _normalize_confusables(label.replace("-", ""))
    for od, org in official.items():
        ol = _label(od)
        if len(ol) < 5:
            continue
        if nl == ol and label != ol:
            return od, org.name
        if _lev(label.replace("-", ""), ol, 2) <= 1 and label.replace("-", "") != ol:
            return od, org.name
    return None


def brand_tokens_in_host(host: str, org: Org) -> bool:
    tokens = set(re.split(r"[.\-_]", host))
    for d in org.domains:
        if _label(d) in tokens:
            return True
    for a in org.aliases:
        a2 = a.lower().replace(" ", "")
        if len(a2) >= 3 and a2 in tokens:
            return True
    return False


_SENSITIVE = {
    "adult": {"substr": ("porn", "xxx", "hentai", "xvideo", "xhamster", "xnxx", "redtube", "youporn"),
              "tokens": {"sex", "sexy", "nude", "nudes", "milf", "escort", "escorts", "camgirl", "camgirls", "nsfw", "onlyfans"},
              "label": "Address suggests adult content"},
    "gambling": {"substr": (), "tokens": {"casino", "slots", "betting", "poker", "jackpot", "bet365"},
                 "label": "Address suggests online gambling"},
    "piracy": {"substr": ("warez", "keygen"), "tokens": {"torrent", "torrents", "cracked", "123movies", "putlocker", "freemovies"},
               "label": "Address suggests pirated or cracked content"},
}


def sensitive_category(url: str) -> tuple[str, str] | None:
    """Heuristic only: keyword match on the address. VERITAS never opens the page."""
    low = url.lower()
    tokens = set(re.findall(r"[a-z0-9]+", low))
    for key, d in _SENSITIVE.items():
        if any(s in low for s in d["substr"]) or tokens & d["tokens"]:
            return key, d["label"]
    return None


def analyze_url(url: str, claimed_orgs: list[Org]) -> list[TechnicalSignal]:
    sigs: list[TechnicalSignal] = []
    host = host_of(url)
    if not host:
        return sigs
    ip = literal_ip(host)
    raw = url.strip()
    scheme_m = re.match(r"(?i)^([a-z][a-z0-9+.-]*)://", raw)
    scheme = scheme_m.group(1).lower() if scheme_m else None
    reg = registrable_domain(host)
    tld = reg.split(".")[-1]

    def add(id_, label, weight, detail):
        sigs.append(TechnicalSignal(id=id_, label=label, weight=weight, detail=detail, subject=url[:200]))

    cat = sensitive_category(url)
    if cat:
        add("sensitive_content_category", cat[1] + " (heuristic)", 0.14,
            "The words in this address suggest a category (adult, gambling or pirated content) that is more often tied to "
            "aggressive ads, fake download buttons, scams and malware. This is a keyword heuristic: VERITAS did not open the "
            "page and cannot confirm what is actually there. It is a caution, not a finding of fraud.")

    if reg in FREEMAIL_DOMAINS and not claimed_orgs:
        return sigs  # e.g. 'gmail.com' in a header: a well-known mail provider, not a link to scrutinize

    if ip is not None:
        add("ip_literal_host", "Link points to a raw IP address", 0.35,
            "Legitimate organizations almost always use a domain name rather than a bare IP address.")
        return sigs

    if "@" in raw.split("//", 1)[-1].split("/", 1)[0]:
        add("userinfo_trick", "Link contains '@' before the real host", 0.35,
            "Text before '@' in a URL is ignored by the browser, which can disguise the true destination.")

    if host.startswith("xn--") or ".xn--" in host or any(ord(c) > 127 for c in host):
        try:
            shown = host.encode("ascii").decode("idna")
        except Exception:
            shown = host
        add("idn_homograph", "Internationalized (look-alike character) domain", 0.35,
            f"The host uses non-ASCII/punycode characters (decodes to '{shown}'), a common look-alike technique.")

    if reg in SHORTENERS or host in SHORTENERS:
        add("url_shortener", "Shortened link hides the destination", 0.2,
            "The final destination cannot be seen without opening the link. Do not open it to find out.")

    if scheme == "http":
        add("no_https", "Link does not use HTTPS", 0.1, "The link uses unencrypted HTTP.")

    if tld in SUSPICIOUS_TLDS:
        add("suspicious_tld", f"Uncommon top-level domain (.{tld})", 0.2,
            f".{tld} is frequently used in throwaway or abusive domains. This is a heuristic, not proof.")

    sub_labels = host[: -len(reg)].rstrip(".").split(".") if host != reg else []
    if len(sub_labels) >= 3:
        add("excess_subdomains", "Unusually deep subdomain chain", 0.12,
            "Long subdomain chains are often used to push a trusted-looking name to the left of the real domain.")

    bait = sorted({w for w in re.split(r"[.\-_]", host) if w in BAIT_WORDS})
    if bait and reg not in all_official_domains():
        add("bait_keywords", "Domain contains account-security wording", 0.15,
            f"Words such as {', '.join(bait[:4])} are common in deceptive domains.")

    # brand / lookalike checks against the bundled reference
    official = all_official_domains()
    if reg not in official:
        lk = lookalike_of(reg)
        if lk:
            add("lookalike_domain", f"Domain imitates {lk[1]}", 0.5,
                f"'{reg}' is very close to the official domain '{lk[0]}' but is not it.")
        else:
            for org in ORGS:
                if brand_tokens_in_host(host, org):
                    add("brand_in_unrelated_domain", f"Uses the name '{org.name}' on an unrelated domain", 0.45,
                        f"The host '{host}' contains the {org.name} name but its registrable domain is '{reg}', "
                        f"not one of {', '.join(org.domains)}.")
                    break

    # claimed organization vs link domain (skip if a stronger brand/lookalike signal already covers it)
    already = any(s.id in ("lookalike_domain", "brand_in_unrelated_domain") for s in sigs)
    for org in claimed_orgs:
        if reg in SHORTENERS or already:
            continue
        if not host_matches_official(host, org):
            add("claimed_org_domain_mismatch", f"Link does not belong to {org.name}", 0.4,
                f"The message references {org.name}, but this link goes to '{reg}', which is not in the bundled "
                f"list of official {org.name} domains ({', '.join(org.domains)}).")
            break
    return sigs


def analyze_email(addr: str, claimed_orgs: list[Org]) -> list[TechnicalSignal]:
    sigs: list[TechnicalSignal] = []
    dom = addr.split("@")[-1].lower()
    reg = registrable_domain(dom)

    def add(id_, label, weight, detail):
        sigs.append(TechnicalSignal(id=id_, label=label, weight=weight, detail=detail, subject=addr))

    for org in claimed_orgs:
        if host_matches_official(dom, org):
            return sigs
    if claimed_orgs and reg in FREEMAIL_DOMAINS:
        add("freemail_for_org", "Organization contact uses a free email service", 0.3,
            f"The message refers to {claimed_orgs[0].name} but the contact address is on {reg}, a free email provider.")
    elif claimed_orgs and reg not in all_official_domains():
        add("sender_domain_mismatch", "Contact email domain does not match the organization", 0.35,
            f"The message refers to {claimed_orgs[0].name} but the contact address uses '{reg}', which is not one of "
            f"its official domains in the bundled list.")
    lk = lookalike_of(reg)
    if lk:
        add("lookalike_email_domain", f"Email domain imitates {lk[1]}", 0.45,
            f"'{reg}' is very close to '{lk[0]}'.")
    return sigs
