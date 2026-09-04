from .gemini_client import safe_generate_json
from django.conf import settings

FALLBACK_SUBJECT = "Regarding your recent payment"
FALLBACK_BODY_TEMPLATE = "Hi {name}, we noticed an issue with a payment of ₹{amount}. Please follow up."


def compose_email(customer, revenue_event, diagnosis):
    """
    Gemini writes the actual email copy, honoring the customer's language
    preference (including Hinglish). Falls back to a static template if
    the call fails — the email always sends either way.
    """
    tone_instruction = (
        "Write in natural Hinglish (Hindi-English mix, as commonly used in India), "
        "friendly and respectful."
        if customer.language_preference == "hi-en"
        else "Write in clear, professional English."
    )

    prompt = f"""Write a short payment-recovery email for an Indian customer.

Customer name: {customer.name}
Amount at risk: ₹{revenue_event.amount}
Root cause (internal, don't mention explicitly): {diagnosis.root_cause}
Context: {diagnosis.explanation}

{tone_instruction}
Keep it under 80 words. Be helpful, not pushy. No subject line prefix like "Subject:".

Return JSON: {{"subject": "<short subject line>", "body": "<email body>"}}"""

    result = safe_generate_json(prompt, model=settings.GEMINI_FAST_MODEL)

    if result and result.get("subject") and result.get("body"):
        return result["subject"], result["body"]

    return FALLBACK_SUBJECT, FALLBACK_BODY_TEMPLATE.format(name=customer.name, amount=revenue_event.amount)