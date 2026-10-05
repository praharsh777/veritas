"""Seeded demo scenarios. All domains/numbers are fictional. Used for the gallery, demos, and tests."""
from __future__ import annotations

SCENARIOS: list[dict] = [
    {
        "id": "bank-suspension",
        "title": "Bank account suspension",
        "channel": "SMS",
        "blurb": "Urgent text claiming your account will be suspended.",
        "expect_category": "bank_account_alert",
        "expect_level": "high_risk",
        "text": (
            "Chase Alert: Unusual sign-in detected. Your account will be suspended in 30 minutes. "
            "Verify now: http://chase-secure-verify.top/login to avoid a permanent lock. "
            "Reply with the 6-digit code we send you."
        ),
    },
    {
        "id": "job-registration-fee",
        "title": "Job offer with registration fee",
        "channel": "Email",
        "blurb": "Remote role, instant offer, and a 'refundable' fee.",
        "expect_category": "job_offer",
        "expect_level": "high_risk",
        "text": (
            "From: hr.recruitment.team@gmail.com\n"
            "Subject: Job Offer - Remote Data Entry Associate\n\n"
            "Congratulations! You have been selected for a work from home position paying $45 per hour, no experience required. "
            "Your offer letter is attached. To secure your position, please pay a refundable registration fee of $120 via Zelle "
            "for your training kit. Do not tell anyone at your current job. Our interview will be conducted on Telegram, "
            "message us at +1 415 555 0132."
        ),
    },
    {
        "id": "support-otp",
        "title": "Fake customer support asking for OTP",
        "channel": "Phone / chat",
        "blurb": "Agent asks for a code and remote access.",
        "expect_category": "tech_support",
        "expect_level": "high_risk",
        "text": (
            "This is Microsoft Support. Your computer is infected with a virus and your account has been compromised. "
            "Please install AnyDesk so our technician can get remote access right now, and read out the verification code "
            "we just sent to your phone. Do not share this with anyone."
        ),
    },
    {
        "id": "invoice-redirection",
        "title": "Invoice with changed bank details",
        "channel": "Email",
        "blurb": "A familiar vendor suddenly has new payment details.",
        "expect_category": "invoice_payment",
        "expect_level": "high_risk",
        "text": (
            "From: accounts@northwind-supplies.co\n"
            "Subject: Updated payment instructions - Invoice 4471\n\n"
            "Hi, as discussed, we have changed our bank account details. Please remit the outstanding balance of $18,450.00 "
            "for invoice 4471 to the new account below by end of day tomorrow. New routing number: 021000089, account 4400125512. "
            "Please keep this confidential until the payment clears and do not call our old line."
        ),
    },
    {
        "id": "delivery-fee",
        "title": "Delivery redelivery fee",
        "channel": "SMS",
        "blurb": "Parcel 'on hold' until you pay a small fee.",
        "expect_category": "delivery",
        "expect_level": "high_risk",
        "text": (
            "USPS: Your package could not be delivered due to an incomplete address. "
            "Pay a redelivery fee of $1.95 within 24 hours at usps-redelivery-track.xyz/pay or your parcel will be returned."
        ),
    },
    {
        "id": "ai-impersonation",
        "title": "AI voice / social-media impersonation",
        "channel": "Social DM",
        "blurb": "'It's me' from a new number, voice note, urgent gift cards.",
        "expect_category": "impersonation",
        "expect_level": "high_risk",
        "text": (
            "Hi it's me, I lost my phone so this is my new number. I'm in an emergency and need help right now. "
            "I'll send a voice message in a minute. Can you buy 4 Apple gift cards for me today and send me the codes? "
            "Please don't tell mom, I'll pay you back tonight."
        ),
    },
    {
        "id": "unknown-recruiter",
        "title": "Unverified recruiter on LinkedIn",
        "channel": "Social DM",
        "blurb": "Not clearly a scam, but the sender cannot be verified.",
        "expect_category": "job_offer",
        "expect_level": "needs_verification",
        "text": (
            "Hello, I'm a recruiter with Brightpath Talent. We came across your profile and you have been selected for a "
            "remote project coordinator role. Please message us on WhatsApp at +1 628 555 0148 to continue the interview "
            "process. Positions are filling quickly."
        ),
    },
    {
        "id": "legit-meeting",
        "title": "Ordinary meeting reminder (control)",
        "channel": "Email",
        "blurb": "A benign message — shows VERITAS does not cry wolf.",
        "expect_category": "unclassified",
        "expect_level": "low_risk_signals",
        "text": (
            "Hi team, a reminder that our weekly planning meeting is tomorrow at 10:00 in the second-floor conference room. "
            "Please bring your updated notes. The agenda is in the shared folder we used last week. Thanks, Priya"
        ),
    },
]

BY_ID = {s["id"]: s for s in SCENARIOS}
