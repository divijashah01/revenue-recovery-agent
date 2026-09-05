import requests
from django.conf import settings
from .base import ChannelResult


def send_whatsapp_template(to_phone, template_name, params=None):
    """
    Real Meta WhatsApp Cloud API call. While using the free test number,
    `to_phone` must be a number you've added as a verified test recipient
    in Meta Business Manager, or this will fail with a permission error.
    """
    url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.replace("+", ""),
        "type": "template",
        "template": {"name": template_name, "language": {"code": "en"}},
    }
    if params:
        payload["template"]["components"] = [
            {"type": "body", "parameters": [{"type": "text", "text": p} for p in params]}
        ]

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return ChannelResult(success=True, detail=response.json(), cost=0.145)
    except requests.RequestException as e:
        detail = e.response.json() if getattr(e, "response", None) is not None else str(e)
        return ChannelResult(success=False, detail=detail, cost=0.0)

def send_whatsapp_personalized(to_phone, message_text, fallback_template, fallback_params):
    """Tries the AI-personalized template first, falls back to the fixed
    approved template if the new template isn't approved yet or fails."""
    if message_text:
        result = send_whatsapp_template(to_phone, "personalized_recovery_message", params=[message_text])
        if result.success:
            return result
    return send_whatsapp_template(to_phone, fallback_template, params=fallback_params)