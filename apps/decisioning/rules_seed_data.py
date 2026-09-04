"""
Seed values for InterventionRule. base_recovery_probability figures are
documented assumptions for cold-start — see README > Research Notes.
They're stored in the DB (not hardcoded in logic) specifically so they can
be recalibrated from observed InterventionAttempt outcomes over time
without touching code.
"""

RULES = [
    # payment_failure root causes
    ("insufficient_funds", "retry_payment", 0.15, "Delayed retry after payday cycle"),
    ("insufficient_funds", "send_payment_link", 0.35, "Lets customer use a different funding source"),
    ("insufficient_funds", "whatsapp_nudge", 0.25, "Reminder nudge, low cost"),

    ("card_declined", "send_payment_link", 0.40, "New card / different payment method"),
    ("card_declined", "whatsapp_nudge", 0.20, "Reminder nudge"),

    ("incorrect_details", "send_payment_link", 0.45, "Fresh checkout avoids repeating the typo"),
    ("incorrect_details", "retry_payment", 0.10, "Rarely fixes itself without new details"),

    ("auth_failed", "retry_payment", 0.30, "OTP failures are often transient"),
    ("auth_failed", "whatsapp_nudge", 0.20, "Reminder to retry with correct OTP"),

    ("bank_technical_issue", "retry_payment", 0.50, "Bank-side outage, likely to resolve"),
    ("bank_technical_issue", "whatsapp_nudge", 0.15, "Backup nudge if retry window passes"),

    ("unknown_decline", "send_payment_link", 0.25, "Generic fallback"),
    ("unknown_decline", "whatsapp_nudge", 0.15, "Generic fallback"),

    # checkout_abandonment root causes
    ("abandoned_at_payment", "whatsapp_nudge", 0.35, "Highest-intent abandonment point"),
    ("abandoned_at_payment", "send_payment_link", 0.30, "Direct path back to checkout"),
    ("abandoned_at_payment", "email_reminder", 0.15, "Lower cost fallback"),

    ("abandoned_at_shipping", "email_reminder", 0.20, "Mid-funnel, lower urgency"),
    ("abandoned_at_shipping", "whatsapp_nudge", 0.25, "Mid-funnel nudge"),

    ("abandoned_at_cart", "email_reminder", 0.10, "Low-intent, cheapest channel first"),
    ("abandoned_at_cart", "whatsapp_nudge", 0.15, "Slightly stronger nudge"),

    ("abandoned_at_review", "whatsapp_nudge", 0.30, "High-intent, near-conversion"),
    ("abandoned_at_review", "send_payment_link", 0.28, "Direct path back"),

    # overdue_invoice root causes
    ("recently_overdue", "email_reminder", 0.30, "Gentle first touch"),
    ("recently_overdue", "whatsapp_nudge", 0.35, "Higher open-rate than email"),
    ("recently_overdue", "promise_to_pay", 0.25, "Structured commitment ask"),

    ("moderately_overdue", "whatsapp_nudge", 0.25, "Escalating tone"),
    ("moderately_overdue", "promise_to_pay", 0.30, "Structured commitment ask"),
    ("moderately_overdue", "sms_reminder", 0.15, "Backup channel"),

    ("severely_overdue", "promise_to_pay", 0.20, "Last automated attempt"),
    ("severely_overdue", "escalate_human", 0.40, "B2B receivables need a human at this stage"),

    # payment_degradation root causes (predictive, pre-emptive intervention)
    ("degradation_high_risk", "send_payment_link", 0.30, "Pre-emptive: refresh payment method before hard failure"),
    ("degradation_high_risk", "whatsapp_nudge", 0.25, "Pre-emptive reminder before failure occurs"),
    ("degradation_moderate_risk", "whatsapp_nudge", 0.18, "Lighter-touch pre-emptive nudge, lower confidence"),
    ("degradation_moderate_risk", "email_reminder", 0.10, "Cheapest pre-emptive touch given ambiguity"),
]