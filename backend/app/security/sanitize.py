"""Input normalisation, redaction, and prompt-injection detection.

Analysed content is *data*. It is never concatenated into system prompts, never
allowed to select tools, and any attempt to address the AI is itself reported as a signal.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁠﻿]")
_WS = re.compile(r"[ \t]+")

# Phrases that address an AI/assistant rather than a human reader of a normal message.
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts?|rules)",
    r"disregard (all |any |the )?(previous|prior|above|earlier|system)",
    r"forget (everything|all|your) (instructions|rules|above)",
    r"(reveal|show|print|repeat|output) (your |the )?(system|hidden|initial) (prompt|instructions|message)",
    r"you are (now|no longer) (an?|the)\b",
    r"\bnew (system )?(instructions?|rules?)\s*:",
    r"(mark|classify|rate|label|report) (this|it|the message)( as| to be| as being)? (safe|legitimate|not (a )?scam|low[- ]risk|trusted)",
    r"(do not|don't) (flag|report|warn)",
    r"\bas an? (ai|assistant|language model)\b.{0,40}\b(must|should|will)\b",
    r"<\|?(im_start|im_end|system|assistant|endoftext)\|?>",
    r"\[/?(INST|SYS)\]",
    r"</?(untrusted_message|system|instructions?)>",
    r"\b(call|invoke|run|execute|use) (the |a )?(tool|function|browser|fetch|http)\b",
    r"\bset (the )?risk(_score| score)? to\b",
]
_INJECTION_RE = [re.compile(p, re.I | re.S) for p in INJECTION_PATTERNS]


def normalize_text(text: str, max_chars: int) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = _CONTROL.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(_WS.sub(" ", ln).strip() for ln in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:max_chars]


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8", "replace")
    return hashlib.sha256(data).hexdigest()


def detect_injection(text: str) -> list[str]:
    """Return short excerpts of text that attempt to instruct an AI system."""
    hits: list[str] = []
    for rx in _INJECTION_RE:
        m = rx.search(text)
        if m:
            s = max(0, m.start() - 15)
            hits.append(text[s : m.end() + 25].replace("\n", " ").strip()[:140])
    return hits


def fence_for_llm(text: str, limit: int = 8000) -> str:
    """Prepare untrusted text for placement inside a delimited data block."""
    text = text[:limit]
    # neutralise anything that looks like our delimiter or chat-role markup
    text = re.sub(r"</?\s*untrusted_message\s*>", "[delimiter removed]", text, flags=re.I)
    text = re.sub(r"<\|[^|>]*\|>", "[token removed]", text)
    return text


_EMAIL = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
_LONGNUM = re.compile(r"\d(?:[\d\s-]{5,}\d)")


def redact_preview(text: str, limit: int = 140) -> str:
    """Preview safe for storage/logging: masks emails and long digit runs (cards, OTPs, phones)."""
    t = _EMAIL.sub(lambda m: f"{m.group(1)}***@{m.group(2)}", text.replace("\n", " "))
    t = _LONGNUM.sub(lambda m: "#" * min(len(m.group(0)), 6), t)
    t = re.sub(r"\b\d{4,8}\b", "####", t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:limit] + "…") if len(t) > limit else t


def validate_image_magic(data: bytes) -> str | None:
    """Return a mime type for allowed image formats by magic bytes, else None."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None
