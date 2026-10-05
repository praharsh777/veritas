# VERITAS demo script (≈3 minutes)

Setup: backend + frontend running, history cleared (`History → Clear all`), browser at `/scenarios`. No API key needed.

**0:00 — Hook (15s).** "Everyone has gotten this text. Most tools tell you 'scam: 92%'. That doesn't help someone with a
30-minute countdown in their head. VERITAS helps you *verify before you act*."

**0:15 — Screenshot in (30s).** Scenarios → *Bank account suspension* → **Analyze as screenshot**.
Say: "A screenshot goes in. VERITAS extracts the text, links, who it claims to be, and what it wants."

**0:45 — Report (45s).** Point to: verdict **High Risk**, Risk 85 vs **separate** Confidence 95. Open *Why we think this*:
urgency, fear, code request, and the technical signals — the link imitates Chase on a `.top` domain. Click one reason to
show the exact quote. "Every reason is tagged: observed in the message, a fixed rule, external evidence, or AI inference."

**1:30 — Evidence (30s).** **Open evidence**: "Is `chase-secure-verify.top` an official Chase domain? — does not match
reference." Show the limits line: "Bundled reference, not live, not proof." "We never claim a bank confirmed anything."

**2:00 — Climax: Verify Before You Act (30s).** "The score isn't the point — this is." Show: *Go to Chase yourself — type
`chase.com`*, call the number on your card, **Do not** list (never share codes, never use the link).

**2:30 — Generalizes (30s).** Back to gallery → *Invoice with changed bank details* (or *Job offer with registration fee*).
"Same engine, different fraud: it flags the **payment redirection** and says **Unable to independently verify** the vendor
and tells you to call a number you already trust." Optionally run *Ordinary meeting reminder* → Low-Risk Signals, "it doesn't cry wolf".

**2:55 — Close.** "VERITAS does not ask you to trust AI. It helps you verify before you act."

## If something goes wrong
- Backend offline badge in the nav → start `uvicorn app.main:app --port 8000`.
- Screenshot button missing → run `python backend/scripts/make_demo_screenshots.py`.
- Add `ANTHROPIC_API_KEY` to show the AI-reasoning panel (optional; demo works without).
