from datetime import timedelta
from django.utils import timezone
from .models import InterventionAttempt

MAX_ATTEMPTS_PER_EVENT = 3
COOLDOWN_HOURS = 6
ESCALATION_AMOUNT_THRESHOLD = 50000  # ₹ — above this, prefer human escalation over further automation
MINIMUM_VIABLE_AMOUNT = 50           # ₹ — below this, no action is worth the operational overhead

def can_attempt(revenue_event):
    """
    The compliant-escalation / stopping-rule gate. Every decision must pass
    through here before the optimizer is even allowed to pick an action.
    Returns (allowed: bool, reason: str)
    """
    if revenue_event.customer.opted_out:
        return False, "customer_opted_out"

    if float(revenue_event.amount) < MINIMUM_VIABLE_AMOUNT:
        return False, "below_minimum_recovery_threshold"

    attempts = InterventionAttempt.objects.filter(revenue_event=revenue_event)
    attempt_count = attempts.count()

    if attempt_count >= MAX_ATTEMPTS_PER_EVENT:
        return False, "max_attempts_reached"

    last_attempt = attempts.order_by("-attempted_at").first()
    if last_attempt:
        cooldown_until = last_attempt.attempted_at + timedelta(hours=COOLDOWN_HOURS)
        if timezone.now() < cooldown_until:
            return False, "cooldown_active"

    return True, "ok"