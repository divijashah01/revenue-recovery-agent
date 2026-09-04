from apps.decisioning.models import InterventionAttempt
from apps.audit.services import log_audit
from .channels.whatsapp import send_whatsapp_template
from .channels.email_channel import send_email_reminder
from .channels.sms_channel import send_sms_reminder
from apps.intelligence.message_composer import compose_email
from apps.intelligence.escalation_briefing import generate_escalation_brief

WHATSAPP_ACTIONS = {"whatsapp_nudge", "send_payment_link", "promise_to_pay"}
EMAIL_ACTIONS = {"email_reminder"}
SMS_ACTIONS = {"sms_reminder"}

TEMPLATE_MAP = {
    "whatsapp_nudge": "payment_reminder_nudge",
    "send_payment_link": "payment_link_share",
    "promise_to_pay": "promise_to_pay_request",
}


def execute_decision(revenue_event):
    """
    Takes a 'decided' event, fires the chosen action through the right
    channel, records an InterventionAttempt, and logs the audit trail.
    """
    decision = getattr(revenue_event, "decision", None)
    if decision is None:
        return None

    action = decision.chosen_action

    if action == "stop":
        return None

    if action == "escalate_human":
        attempt = InterventionAttempt.objects.create(revenue_event=revenue_event, action=action, outcome="pending")
        revenue_event.status = "escalated"
        revenue_event.save(update_fields=["status", "updated_at"])
        brief = generate_escalation_brief(revenue_event)
        log_audit(revenue_event, "action_attempted", {"action": action, "brief": brief})
        return attempt

    if action == "retry_payment":
        # In a full integration this calls Razorpay's retry/re-authorization
        # flow directly; logged as pending here since retry outcomes arrive
        # asynchronously via a future payment.captured webhook.
        attempt = InterventionAttempt.objects.create(revenue_event=revenue_event, action=action, outcome="pending")
        log_audit(revenue_event, "action_attempted", {"action": action})
        return attempt

    attempt = InterventionAttempt.objects.create(revenue_event=revenue_event, action=action, outcome="pending")
    customer = revenue_event.customer
    result = None

    if action in WHATSAPP_ACTIONS:
        template = TEMPLATE_MAP.get(action, "payment_reminder_nudge")
        result = send_whatsapp_template(customer.phone, template, params=[customer.name, str(revenue_event.amount)])
    elif action in EMAIL_ACTIONS:
        subject, body = compose_email(customer, revenue_event, revenue_event.diagnosis)
        result = send_email_reminder(customer.email, subject, body)
    elif action in SMS_ACTIONS:
        result = send_sms_reminder(customer.phone, f"₹{revenue_event.amount} payment pending. Please complete.")

    if result:
        attempt.outcome = "success" if result.success else "failed"
        attempt.save(update_fields=["outcome"])
        revenue_event.status = "in_progress"
        revenue_event.save(update_fields=["status", "updated_at"])
        log_audit(revenue_event, "action_attempted", {
            "action": action,
            "channel_result": str(result.detail)[:500],
            "cost": result.cost,
        })

    return attempt