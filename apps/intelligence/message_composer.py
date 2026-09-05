from .gemini_client import safe_generate_json
from django.conf import settings
from .cost_guard import llm_worth_it

FALLBACK_SUBJECT = "Regarding your recent payment"
FALLBACK_BODY_TEMPLATE = "Hi {name}, we noticed an issue with a payment of ₹{amount}. Please follow up."


def compose_email(customer, revenue_event, diagnosis):
    if not llm_worth_it(revenue_event):
        return FALLBACK_SUBJECT, FALLBACK_BODY_TEMPLATE.format(name=customer.name, amount=revenue_event.amount)

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

def compose_whatsapp_message(customer, revenue_event, diagnosis):
    """
    Full personalized WhatsApp copy for the single-variable template. Falls
    back to None (caller uses the old fixed templates) on any failure or
    cost-guard block — never blocks the send.
    """
    if not llm_worth_it(revenue_event):
        return None

    tone_instruction = (
        "Natural Hinglish, friendly, respectful, ONE line, no line breaks."
        if customer.language_preference == "hi-en"
        else "Clear professional English, ONE line, no line breaks."
    )
    prompt = f"""Write a single-line WhatsApp message (max 25 words, no line breaks)
for {customer.name} about a payment of ₹{revenue_event.amount}. Context: {diagnosis.explanation}
{tone_instruction} End with a short call to action."""

    from .gemini_client import safe_generate_text
    from django.conf import settings
    text = safe_generate_text(prompt, model=settings.GEMINI_FAST_MODEL)
    return text.replace("\n", " ").strip() if text else None