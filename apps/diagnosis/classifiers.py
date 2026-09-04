from django.utils import timezone
from .models import Diagnosis
from apps.audit.services import log_audit
from apps.intelligence.diagnosis_reasoner import reason_about_ambiguous_case

# Maps Razorpay's real error_reason values to our root-cause codes.
PAYMENT_FAILURE_MAP = {
    "insufficient_funds": ("insufficient_funds", "Customer's account/card had insufficient balance", 1.0),
    "card_declined": ("card_declined", "Issuing bank declined the card", 0.9),
    "incorrect_cvv": ("incorrect_details", "Customer entered incorrect card details", 1.0),
    "authentication_failed": ("auth_failed", "3D Secure / OTP authentication failed", 1.0),
    "bank_technical_error": ("bank_technical_issue", "Issuing bank had a technical/downtime issue", 1.0),
    "bank_not_available": ("bank_technical_issue", "Bank unavailable at time of transaction", 1.0),
    "payment_failed": ("unknown_decline", "Bank declined without a specific reason", 0.5),
}

STAGE_TO_ROOT_CAUSE = {
    "payment": ("abandoned_at_payment", "Customer dropped off at the final payment step", 0.9),
    "shipping": ("abandoned_at_shipping", "Customer dropped off entering shipping details", 0.7),
    "cart": ("abandoned_at_cart", "Customer dropped off early, still browsing cart", 0.5),
    "review": ("abandoned_at_review", "Customer dropped off at final order review", 0.85),
}


def diagnose(revenue_event):
    """Classifies a RevenueEvent into a root cause and writes the Diagnosis row."""

    if revenue_event.event_type == "payment_failure":
        if revenue_event.error_reason in PAYMENT_FAILURE_MAP:
            root_cause, explanation, confidence = PAYMENT_FAILURE_MAP[revenue_event.error_reason]
        else:
            root_cause, explanation, confidence = reason_about_ambiguous_case(
                revenue_event, "unmapped_failure", f"Unrecognized error_reason: {revenue_event.error_reason}"
            )

    elif revenue_event.event_type == "checkout_abandonment":
        stage = revenue_event.checkout_session.stage if revenue_event.checkout_session else "cart"
        root_cause, explanation, confidence = STAGE_TO_ROOT_CAUSE.get(
            stage, ("abandoned_at_cart", "Unknown abandonment stage, defaulted to cart", 0.4)
        )

    elif revenue_event.event_type == "overdue_invoice":
        days_overdue = 0
        if revenue_event.invoice:
            days_overdue = (timezone.now().date() - revenue_event.invoice.due_date).days

        if days_overdue < 7:
            root_cause, explanation, confidence = "recently_overdue", f"{days_overdue} days overdue", 1.0
        elif days_overdue < 30:
            root_cause, explanation, confidence = "moderately_overdue", f"{days_overdue} days overdue", 1.0
        else:
            root_cause, explanation, confidence = "severely_overdue", f"{days_overdue} days overdue", 1.0

    elif revenue_event.event_type == "payment_degradation":
        payload = revenue_event.raw_payload or {}
        score = payload.get("risk_score", 0.0)
        signals = payload.get("signals", {})

        if score >= 0.7:
            root_cause = "degradation_high_risk"
            explanation = f"High degradation risk (score={score}): {signals}"
            confidence = score
        else:
            root_cause, explanation, confidence = reason_about_ambiguous_case(
                revenue_event, "degradation_moderate_risk", f"Moderate risk (score={score}): {signals}"
            )

    else:
        root_cause, explanation, confidence = "unknown", "Unrecognized event type", 0.1

    diagnosis = Diagnosis.objects.create(
        revenue_event=revenue_event,
        root_cause=root_cause,
        explanation=explanation,
        confidence=confidence,
    )

    revenue_event.status = "diagnosed"
    revenue_event.save(update_fields=["status", "updated_at"])

    log_audit(revenue_event, "diagnosed", {
        "root_cause": diagnosis.root_cause,
        "explanation": diagnosis.explanation,
        "confidence": diagnosis.confidence,
    })

    return diagnosis