# VERITAS — Devpost copy

**Tagline:** Verify before you act. An evidence-first digital trust layer for scams, impersonation and fraud.

## Inspiration
People don't get scammed because they can't spell "phishing" — they get scammed in a 30-second window of fear, urgency or
hope. Classifiers that say "92% scam" don't give a frightened person a safe next move.

## What it does
Paste a message, drop a screenshot, or enter a link. VERITAS extracts who it claims to be and what it wants, runs
social-engineering and URL/domain checks in parallel, cross-checks identity claims, and returns a report with **risk and
confidence kept separate**, every reason labelled by provenance (observed / rule / external evidence / AI inference), and a
**Verify Before You Act** plan: an independent route to confirm (never the link in the message), what to do, what not to do,
and where to report. When it can't verify something it says **"Unable to independently verify."**

## How we built it
Next.js + TypeScript + Tailwind frontend; FastAPI backend with modular services (extraction, signals, technical checks,
verification, scoring, actions). A provider abstraction supports Claude (text + vision) and any OpenAI-compatible/open-source
model, and the whole pipeline also runs offline. Model output is schema-validated, quote-verified and score-bounded.

## Security by design
Prompt-injection defense (data-fenced input, allow-listed outputs, injection attempts reported as a signal and unable to lower
risk), SSRF-hardened URL handling (live fetch off by default), strict upload validation, redacted storage, no secrets in the
browser. 82 automated tests cover injection, malicious URLs, malformed input, tool failure and the end-to-end scenarios.

## Challenges
Keeping the AI honest: separating deterministic checks from inference, refusing to imply external verification we didn't
perform, and making uncertainty useful instead of hand-wavy.

## What we're proud of
The same engine handles bank phishing, fake job offers with fees, fake support/OTP, invoice payment redirection, delivery scams
and impersonation — and a benign control message stays Low-Risk.

## What's next
Live official-source retrieval with provenance, browser extension, voice/video-call signals, Supabase persistence, a labeled
evaluation set so we can report real precision/recall.

**Built with:** next.js, typescript, tailwind, fastapi, python, pydantic, sqlite, claude-api (optional), pytest
