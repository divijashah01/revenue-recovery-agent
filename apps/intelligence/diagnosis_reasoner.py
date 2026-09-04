from .gemini_client import safe_generate_json
from django.conf import settings

# Bounded output set — Gemini can only ever pick from these, never invent a
# new root cause. This keeps the LLM's contribution to *interpretation*,
# not to expanding the decision space.
AMBIGUOUS_ALLOWED_CAUSES = [
    "insufficient_funds", "card_declined", "incorrect_details", "auth_failed",
    "bank_technical_issue", "unknown_decline",
    "degradation_high_risk", "degradation_moderate_risk", "degradation_low_risk",
]


def reason_about_ambiguous_case(revenue_event, fallback_cause, fallback_explanation):
    """
    Used only for the low-confidence branches (unmapped/unknown payment
    failures, moderate-risk degradation) where the static rule table
    genuinely runs out. Returns (root_cause, explanation, confidence),
    falling back to the deterministic default on any failure.
    """
    context = {
        "event_type": revenue_event.event_type,
        "error_code": revenue_event.error_code,
        "error_reason": revenue_event.error_reason,
        "amount": str(revenue_event.amount),
        "raw_signals": revenue_event.raw_payload,
    }

    prompt = f"""You are a payment-failure diagnosis assistant for an Indian fintech
revenue recovery system. Given this event context, classify the root cause.

Context: {context}

You MUST choose root_cause from exactly this list: {AMBIGUOUS_ALLOWED_CAUSES}

Return JSON: {{"root_cause": "<one from the list>", "explanation": "<one sentence>", "confidence": <0.0-1.0>}}"""

    result = safe_generate_json(prompt, model=settings.GEMINI_FAST_MODEL)

    if result and result.get("root_cause") in AMBIGUOUS_ALLOWED_CAUSES:
        return result["root_cause"], f"[Gemini] {result.get('explanation', '')}", float(result.get("confidence", 0.5))

    return fallback_cause, fallback_explanation, 0.3