"""
Grounded per-message/action costs used by the ROI-aware intervention optimizer.
Sourced from Meta's official WhatsApp Business Platform rate card (India, effective
Jan 2026) and MSG91 published transactional SMS rates. See README > Research Notes
for citations. Treated as constants, not estimates, so recovery-value math is honest.
"""

# WhatsApp Cloud API — India, per delivered template message (INR)
WHATSAPP_UTILITY_COST = 0.145        # reminders, receipts, payment-link nudges
WHATSAPP_MARKETING_COST = 1.09       # not used for recovery flows, just for reference
WHATSAPP_SERVICE_COST = 0.0          # free inside a user-opened 24h window

# Transactional SMS — India, per message (INR), MSG91 published rate
SMS_TRANSACTIONAL_COST = 0.20

# Email — negligible, treated as free for cost modeling
EMAIL_COST = 0.0

# Human agent follow-up (B2B receivables escalation) — modeled assumption,
# not a market rate: ~4 min call at an assumed ₹300/hr agent cost.
HUMAN_AGENT_CALL_COST = 20.0

# Gemini API costs — approximate, India, Sept 2026, flash-lite/flash tiers (see README > Research Notes)
GEMINI_FLASH_LITE_COST_PER_CALL = 0.02   # used for diagnosis reasoning, email/WhatsApp composition
GEMINI_FLASH_COST_PER_CALL = 0.08        # used only for escalation briefs — lower volume, higher reasoning need