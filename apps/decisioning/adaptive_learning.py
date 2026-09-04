from django.db.models import Count, Q
from .models import InterventionRule
from apps.events.models import RevenueEvent

PRIOR_WEIGHT = 5      # treat the seeded probability as if backed by 5 pseudo-observations
MIN_OBSERVATIONS = 3  # don't recalibrate on noise


def recalibrate_probabilities():
    """
    Deterministic Bayesian-style update: posterior = (prior*W + successes) / (W + total).
    Kept fully numeric and auditable on purpose — probability calibration
    is a place where transparency matters more than LLM fluency. This is
    what makes 'determines the right intervention' genuinely adaptive
    instead of frozen at cold-start assumptions.
    """
    changes = []

    for rule in InterventionRule.objects.all():
        completed = RevenueEvent.objects.filter(
            diagnosis__root_cause=rule.root_cause,
            decision__chosen_action=rule.action,
            status__in=["recovered", "in_progress"],
        )
        total = completed.count()
        if total < MIN_OBSERVATIONS:
            continue

        successes = completed.filter(status="recovered").count()
        prior = rule.base_recovery_probability
        posterior = round((prior * PRIOR_WEIGHT + successes) / (PRIOR_WEIGHT + total), 3)

        if abs(posterior - prior) > 0.001:
            changes.append((rule.root_cause, rule.action, prior, posterior, total, successes))
            rule.base_recovery_probability = posterior
            rule.save(update_fields=["base_recovery_probability"])

    return changes