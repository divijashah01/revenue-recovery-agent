from myproject.intervention_costs import (
    WHATSAPP_UTILITY_COST,
    SMS_TRANSACTIONAL_COST,
    EMAIL_COST,
    HUMAN_AGENT_CALL_COST,
)
from .models import InterventionRule, Decision
from .guards import can_attempt, ESCALATION_AMOUNT_THRESHOLD
from apps.audit.services import log_audit

ACTION_COSTS = {
    "retry_payment": 0.0,
    "send_payment_link": WHATSAPP_UTILITY_COST,
    "whatsapp_nudge": WHATSAPP_UTILITY_COST,
    "email_reminder": EMAIL_COST,
    "sms_reminder": SMS_TRANSACTIONAL_COST,
    "promise_to_pay": WHATSAPP_UTILITY_COST,
    "escalate_human": HUMAN_AGENT_CALL_COST,
    "stop": 0.0,
}


def score_candidates(revenue_event, diagnosis):
    """
    Expected value = (recovery probability * amount at risk) - cost of the
    action. This is the core of the ROI-aware optimizer: it won't recommend
    spending ₹20 in agent time to chase a ₹15 invoice.
    """
    rules = InterventionRule.objects.filter(root_cause=diagnosis.root_cause)
    amount = float(revenue_event.amount)

    candidates = []
    for rule in rules:
        cost = ACTION_COSTS.get(rule.action, 0.0)
        expected_value = (rule.base_recovery_probability * amount) - cost
        candidates.append({
            "action": rule.action,
            "recovery_probability": rule.base_recovery_probability,
            "cost": cost,
            "expected_value": round(expected_value, 2),
        })

    candidates.sort(key=lambda c: c["expected_value"], reverse=True)
    return candidates


def decide(revenue_event, diagnosis):
    """
    Full decision flow: guard check first (stopping rules), then ROI scoring.
    Always writes a Decision row with the full candidate list, so every
    outcome is explainable after the fact.
    """
    allowed, reason = can_attempt(revenue_event)

    if not allowed:
        if reason == "max_attempts_reached" and float(revenue_event.amount) >= ESCALATION_AMOUNT_THRESHOLD:
            chosen_action = "escalate_human"
        elif reason in ("customer_opted_out", "max_attempts_reached", "below_minimum_recovery_threshold"):
            chosen_action = "stop"
        else:  # cooldown_active — leave event as-is, do not decide yet
            return None

        decision = Decision.objects.create(
            revenue_event=revenue_event,
            diagnosis=diagnosis,
            chosen_action=chosen_action,
            expected_recovery_probability=None,
            expected_cost=ACTION_COSTS.get(chosen_action, 0),
            expected_value=0,
            candidates_considered=[],
            reason=reason,
        )
    else:
        candidates = score_candidates(revenue_event, diagnosis)

        if not candidates or candidates[0]["expected_value"] <= 0:
            chosen_action = "stop"
            best = {"recovery_probability": None, "cost": 0, "expected_value": 0}
            decision_reason = "no_positive_expected_value_action"
        else:
            best = candidates[0]
            chosen_action = best["action"]
            decision_reason = "best_expected_value"

        decision = Decision.objects.create(
            revenue_event=revenue_event,
            diagnosis=diagnosis,
            chosen_action=chosen_action,
            expected_recovery_probability=best["recovery_probability"],
            expected_cost=best["cost"],
            expected_value=best["expected_value"],
            candidates_considered=candidates,
            reason=decision_reason,
        )

    revenue_event.status = "stopped" if chosen_action == "stop" else "decided"
    revenue_event.save(update_fields=["status", "updated_at"])

    log_audit(revenue_event, "decided", {
        "chosen_action": decision.chosen_action,
        "expected_value": float(decision.expected_value),
        "reason": decision.reason,
    })

    return decision