import json
from django.conf import settings
from google import genai

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def safe_generate_json(prompt, model=None):
    """
    Calls Gemini expecting a strict JSON response. Never raises — on any
    failure (API error, rate limit, malformed JSON) it returns None so
    calling code always has a deterministic rule-based fallback. This is
    what keeps the AI layer additive rather than a single point of failure.
    """
    model = model or settings.GEMINI_FAST_MODEL
    try:
        client = get_client()
        response = client.models.generate_content(
            model=model,
            contents=prompt + "\n\nRespond with ONLY valid JSON, no markdown fences, no preamble.",
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Gemini fallback] {model} call failed: {e}")
        return None


def safe_generate_text(prompt, model=None):
    """Same fail-safe pattern, for free-text output (email body, briefing)."""
    model = model or settings.GEMINI_FAST_MODEL
    try:
        client = get_client()
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini fallback] {model} call failed: {e}")
        return None