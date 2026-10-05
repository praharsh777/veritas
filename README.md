# VERITAS — Personal Digital Trust Layer

**Verify before you act.** ForgeHacks 2026 · AI + Cybersecurity

VERITAS helps a person answer: *"I received this. Can I trust it, what is the evidence, and what should I do before I act?"*
It accepts pasted messages, links, screenshots and `.txt/.eml` files, extracts claims and requests, runs deterministic
security checks alongside optional AI reasoning, cross-checks identity claims, and returns an **evidence-backed report with a
safe, independent verification plan**. It is decision support, not a "scam / not scam" guesser.

![screenshot placeholder](docs/screenshot-report.png)

## Quick start (Windows)

```powershell
cd veritas
./run-dev.ps1          # creates venv, installs deps, starts backend :8000 and frontend :3000
```

Manual:

```bash
# backend
cd backend && python -m venv .venv && . .venv/Scripts/activate   # (Linux/macOS: .venv/bin/activate)
pip install -r requirements.txt Pillow
cp .env.example .env                  # optional: add ANTHROPIC_API_KEY for the AI layer + vision OCR
uvicorn app.main:app --port 8000
# frontend
cd frontend && npm install && npm run dev      # http://localhost:3000
```

**Works with no API key.** Without a key the full deterministic pipeline runs (rules, URL/domain analysis, reference
cross-check, scoring, action plan) and the UI says the AI layer is off. The seeded demo screenshots use bundled
transcription fixtures, so the 2–4 minute demo never depends on external services.

Tests: `cd backend && pytest -q` (82 tests). Frontend type-check/build: `cd frontend && npm run build`.

## UI notes
Dark and light themes (toggle in the nav; follows your system setting on first visit and remembers your choice, with no flash on
load). Colors are CSS-variable tokens in `frontend/app/globals.css`. Animations (animated risk ring, count-up, staggered report
reveal, scroll reveals, skeleton loaders, looping live demo on the landing page) all respect `prefers-reduced-motion`.

## How it works

```
INPUT → NORMALIZE → EXTRACT → PARALLEL ANALYSIS → EVIDENCE/CROSS-CHECK → RISK MODEL → EXPLANATION → ACTION PLAN → FEEDBACK
                              ├ social-engineering rules (13 signals)
                              ├ URL / domain / sender technical checks
                              └ AI reasoning (optional, validated, bounded)
```

| Module | Responsibility |
|---|---|
| `analysis/extraction.py` | entities, URLs, claims, requested actions/data, deadlines, payment requests, contact channels |
| `analysis/signals.py` | transparent regex rules: urgency, fear, lure, OTP/credential request, advance fee, unconventional payment, payment redirection, remote access, secrecy, authority/AI impersonation, unusual channel, context manipulation, prompt-injection attempts |
| `analysis/technical.py` | look-alike/homograph domains, brand-in-unrelated-domain, raw IPs, `@` tricks, shorteners, risky TLDs, free-mail for organizations, claimed-org vs link mismatch |
| `verification/` | bundled reference of official domains → evidence objects, claim status, "Unable to independently verify" |
| `analysis/scoring.py` | `risk = 1 − Π(1 − wᵢ)` weighted model + a **separate** confidence score |
| `analysis/actions.py` | scenario classification + **Verify Before You Act** plan |
| `providers/` | LLM abstraction: Anthropic (text + vision), any OpenAI-compatible endpoint (e.g. Featherless), or offline |
| `security/` | SSRF guard, normalization, redaction, injection detection |

### Provenance on every conclusion
`observed_input` · `deterministic_rule` · `external_evidence` · `model_inference` — shown as colored badges in the UI.
`external_evidence` is reserved for real live retrievals (optional DNS/redirect inspection). The default official-domain
comparison uses a **bundled reference list** and is labelled "Bundled reference (not live)" with its limits in the evidence drawer.

### Risk vs. confidence
Risk is a communication aid, not a probability. Confidence measures how much independent evidence supports the assessment
(identity checked? links analyzed? OCR used? AI used?). A high-risk result with low confidence says
*"High concern, but verification is incomplete."* Verdict states: **High Risk / Needs Verification / Low-Risk Signals** —
VERITAS never says "safe".

## Security model

- Analyzed content is **data**: never placed in system prompts, delimited in `<untrusted_message>`, delimiter/role tokens
  stripped; the model has no tools and cannot choose URLs.
- Model output is schema-validated; signal ids are allow-listed; quoted evidence must appear **verbatim** in the input or
  it is dropped; AI contribution is capped (≤0.25 weight) and can only add concern. Injection attempts inside a message are
  themselves reported as a signal and cannot lower the score (tested).
- SSRF: only http/https, ports 80/443, no userinfo, hostnames/suffix blocklist, IP-literal forms (decimal/hex/octal/IPv6/
  IPv4-mapped), every DNS answer must be public, redirects re-validated per hop. Live fetching is **off by default**.
- Uploads: magic-byte image validation (PNG/JPEG/WebP), 6 MB / 200 KB limits, binary documents rejected, SVG rejected.
- No `dangerouslySetInnerHTML`; links from messages are rendered as inert text. Provider keys live only in backend env; the
  browser talks to a same-origin proxy (`/api/*`).
- Raw message text is **not persisted** — only a redacted preview (emails/digits masked) and the structured report. Logs hold
  request ids, sizes and timings only.
- Failures degrade honestly: a failed check is shown as failed in the timeline and excluded, never fabricated.

## Seeded scenarios (fictional)
Bank suspension · job offer with registration fee · fake support asking for OTP/remote access · invoice with changed bank
details · delivery redelivery fee · AI/voice-style impersonation · unverified recruiter (Needs Verification) · ordinary meeting
reminder (control → Low-Risk Signals). Regenerate screenshots: `python backend/scripts/make_demo_screenshots.py`.

## Limitations (be upfront with judges)
- The reference list covers ~20 well-known organizations; unknown senders get "Unable to independently verify" by design.
- Heuristic rules will miss novel wording and can false-positive; the scores are not calibrated and no accuracy figure is claimed.
- OCR quality depends on the vision model/Tesseract; synthetic-media detection is limited to *contextual* patterns — VERITAS does
  not analyze audio or video.
- History uses SQLite for the demo (swap `store.py` for Supabase/Postgres in production). No auth/rate-limiting is included.
- Optional live checks inspect redirect headers only and cannot fully eliminate DNS-rebinding risk (hence off by default).

## Responsible use
VERITAS is a safety aid and not a law-enforcement, banking, or cybersecurity authority. Do not rely on it as the sole basis for
financial decisions; confirm through channels you already trust. Report fraud to your bank and local authorities
(e.g. reportfraud.ftc.gov in the US).

See `DEMO_SCRIPT.md` for the 2–4 minute walkthrough and `DEVPOST.md` for submission copy.
