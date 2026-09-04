"""
Deterministic, customer-facing plain-language explanations. Kept static
(not LLM-generated) on purpose — this page must never fail to render
correctly, and money-adjacent customer copy should be predictable.
"""

CUSTOMER_FRIENDLY_REASONS = {
    "insufficient_funds": {
        "en": "Your payment didn't go through because of insufficient balance.",
        "hi-en": "Aapka payment insufficient balance ki wajah se complete nahi ho paaya.",
    },
    "card_declined": {
        "en": "Your card was declined by your bank.",
        "hi-en": "Aapki bank ne is card ko decline kar diya.",
    },
    "incorrect_details": {
        "en": "There was a mismatch in the card details entered.",
        "hi-en": "Card details mein kuch mismatch tha.",
    },
    "auth_failed": {
        "en": "The one-time verification (OTP/3D-Secure) wasn't completed.",
        "hi-en": "OTP ya verification step complete nahi ho paaya.",
    },
    "bank_technical_issue": {
        "en": "Your bank had a temporary technical issue at the time of payment.",
        "hi-en": "Uss waqt aapki bank mein ek technical issue tha.",
    },
    "abandoned_at_payment": {
        "en": "It looks like your order was almost complete — you stopped right at payment.",
        "hi-en": "Aapka order almost complete tha — payment step pe ruk gaya.",
    },
    "recently_overdue": {
        "en": "This invoice recently went past its due date.",
        "hi-en": "Yeh invoice due date se thoda overdue ho gaya hai.",
    },
    "degradation_high_risk": {
        "en": "We noticed some trouble with your recent payment attempts and wanted to help before it fails.",
        "hi-en": "Aapke recent payment attempts mein kuch dikkat dikhi, isliye pehle hi help karna chahte hain.",
    },
}

DEFAULT_REASON_TEXT = {
    "en": "We noticed an issue with a recent payment or invoice.",
    "hi-en": "Humein aapke ek payment ya invoice mein issue dikha.",
}