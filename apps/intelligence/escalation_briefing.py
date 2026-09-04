from .gemini_client import safe_generate_text
from django.conf import settings


def generate_escalation_brief(revenue_event):
    """
    Synthesizes a short human-readable brief for a human agent picking up
    an escalated case — genuine agentic synthesis, kept entirely separate
    from the money decision itself (that already happened deterministically
    before escalation was chosen).
    """
    diagnosis = getattr(revenue_event, "diagnosis", None)
    decision = getattr(revenue_event, "decision", None)
    attempts = revenue_event.attempts.all()

    context = f"""Customer: {revenue_event.customer.name} ({revenue_event.customer.phone})
Amount at risk: ₹{revenue_event.amount}
Event type: {revenue_event.event_type}
Root cause: {diagnosis.root_cause if diagnosis else 'unknown'} - {diagnosis.explanation if diagnosis else ''}
Decision reason: {decision.reason if decision else 'unknown'}
Prior attempts: {[(a.action, a.outcome) for a in attempts]}"""

    prompt = f"""Write a 2-3 sentence briefing for a human recovery agent about to
follow up on this escalated case. Be specific and actionable — what happened,
what's already been tried, and one suggestion for the human's next step.

{context}"""

    brief = safe_generate_text(prompt, model=settings.GEMINI_REASONING_MODEL)

    if brief:
        return brief

    return (
        f"Escalated: {revenue_event.customer.name}, ₹{revenue_event.amount}. "
        f"Root cause: {diagnosis.root_cause if diagnosis else 'unknown'}. "
        f"{len(attempts)} prior automated attempt(s) made. Manual follow-up required."
    )