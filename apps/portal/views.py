from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from apps.audit.services import log_audit
from apps.execution.channels.razorpay_link import create_payment_link
from .models import PortalLink
from .copy import CUSTOMER_FRIENDLY_REASONS, DEFAULT_REASON_TEXT


def portal_view(request, token):
    link = get_object_or_404(PortalLink, token=token)
    event = link.revenue_event
    customer = event.customer
    diagnosis = getattr(event, "diagnosis", None)
    root_cause = diagnosis.root_cause if diagnosis else "unknown"
    lang = customer.language_preference

    reason_text = CUSTOMER_FRIENDLY_REASONS.get(root_cause, {}).get(
        lang, DEFAULT_REASON_TEXT.get(lang, DEFAULT_REASON_TEXT["en"])
    )

    if not link.payment_link_url and event.status not in ("recovered", "stopped") and not customer.opted_out:
        url = create_payment_link(customer, event.amount)
        if url:
            link.payment_link_url = url
            link.save(update_fields=["payment_link_url"])

    context = {
        "event": event,
        "customer": customer,
        "reason_text": reason_text,
        "payment_link_url": link.payment_link_url,
        "opted_out": customer.opted_out,
        "recovered": event.status == "recovered",
    }
    return render(request, "portal/portal.html", context)


def opt_out_view(request, token):
    link = get_object_or_404(PortalLink, token=token)
    if request.method == "POST":
        customer = link.revenue_event.customer
        customer.opted_out = True
        customer.save(update_fields=["opted_out"])
        log_audit(link.revenue_event, "customer_action", {"action": "opted_out_via_portal"})
        messages.success(request, "You will not receive further reminders about this.")
    return redirect("portal-view", token=token)