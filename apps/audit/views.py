from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count
from django.core.paginator import Paginator

from apps.events.models import RevenueEvent
from apps.decisioning.models import Decision

from django.core.management import call_command
from django.contrib import messages as dj_messages
from django.shortcuts import render, get_object_or_404, redirect

from apps.events.models import Customer
from apps.events.services import process_event_immediately

from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import admin_required, agent_required

@admin_required
def dashboard_view(request):
    events = RevenueEvent.objects.all()

    at_risk_total = events.aggregate(total=Sum("amount"))["total"] or 0

    attempted_qs = events.filter(status__in=["in_progress", "recovered", "escalated"])
    attempted_total = attempted_qs.aggregate(total=Sum("amount"))["total"] or 0

    recovered_qs = events.filter(status="recovered")
    recovered_total = recovered_qs.aggregate(total=Sum("recovered_amount"))["total"] or 0

    recovery_rate = round((recovered_total / attempted_total * 100), 1) if attempted_total else 0

    by_type = list(
        events.values("event_type").annotate(count=Count("id"), amount=Sum("amount")).order_by("-amount")
    )
    by_status = list(
        events.values("status").annotate(count=Count("id"), amount=Sum("amount")).order_by("-count")
    )
    by_action = list(
        Decision.objects.exclude(chosen_action="stop")
        .values("chosen_action")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    stop_reasons = list(
        Decision.objects.filter(chosen_action="stop")
        .values("reason")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "at_risk_total": at_risk_total,
        "attempted_total": attempted_total,
        "recovered_total": recovered_total,
        "recovery_rate": recovery_rate,
        "total_events": events.count(),
        "escalated_count": events.filter(status="escalated").count(),
        "stopped_count": events.filter(status="stopped").count(),
        "by_type": by_type,
        "by_status": by_status,
        "by_action": by_action,
        "stop_reasons": stop_reasons,
    }
    return render(request, "audit/dashboard.html", context)


@admin_required
def batch_list_view(request):
    events = RevenueEvent.objects.select_related("customer", "diagnosis", "decision").order_by("-detected_at")

    event_type = request.GET.get("event_type", "")
    status = request.GET.get("status", "")

    if event_type:
        events = events.filter(event_type=event_type)
    if status:
        events = events.filter(status=status)

    paginator = Paginator(events, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "event_type_choices": RevenueEvent.EVENT_TYPE_CHOICES,
        "status_choices": RevenueEvent.STATUS_CHOICES,
        "selected_event_type": event_type,
        "selected_status": status,
    }
    return render(request, "audit/batch_list.html", context)

@login_required
def event_detail_view(request, event_id):
    event = get_object_or_404(
        RevenueEvent.objects.select_related("customer", "diagnosis", "decision"), pk=event_id
    )
    context = {
        "event": event,
        "attempts": event.attempts.all().order_by("attempted_at"),
        "audit_trail": event.audit_trail.all().order_by("created_at"),
    }
    return render(request, "audit/event_detail.html", context)

@admin_required
def shadow_mode_view(request):
    """
    Shows projected recovery for events that are diagnosed + decided but
    NOT yet executed — nothing sent, no money moved. 'Run Live Batch'
    converts the projection into real execution + outcome simulation.
    """
    if request.method == "POST":
        call_command("run_execution")
        call_command("simulate_recovery_outcomes")
        call_command("recalibrate_rules")
        dj_messages.success(request, "Live batch executed — dashboard now reflects real outcomes.")
        return redirect("dashboard")

    decided_events = RevenueEvent.objects.filter(status="decided").select_related("decision")
    at_risk = decided_events.aggregate(total=Sum("amount"))["total"] or 0

    projected_recovery = 0.0
    for event in decided_events:
        decision = getattr(event, "decision", None)
        if decision and decision.expected_recovery_probability:
            projected_recovery += float(decision.expected_recovery_probability) * float(event.amount)

    projected_rate = round((projected_recovery / float(at_risk) * 100), 1) if at_risk else 0

    context = {
        "pending_count": decided_events.count(),
        "at_risk": at_risk,
        "projected_recovery": round(projected_recovery, 2),
        "projected_rate": projected_rate,
    }
    return render(request, "audit/shadow_mode.html", context)

@admin_required
def inject_live_event_view(request):
    if request.method == "POST":
        customer = Customer.objects.create(
            name=request.POST.get("name", "Live Demo Customer"),
            phone=request.POST.get("phone", "+919999999999"),
            email=request.POST.get("email", "demo@example.com"),
            language_preference=request.POST.get("language_preference", "en"),
        )
        event = RevenueEvent.objects.create(
            event_type=request.POST.get("event_type", "payment_failure"),
            customer=customer,
            amount=request.POST.get("amount", 1000),
            source="seed",
            error_code="BAD_REQUEST_ERROR",
            error_reason=request.POST.get("error_reason", "card_declined"),
            raw_payload={"injected_live_demo": True},
        )
        process_event_immediately(event)
        return redirect("event-detail", event_id=event.id)

    context = {"event_type_choices": RevenueEvent.EVENT_TYPE_CHOICES}
    return render(request, "audit/inject_live_event.html", context)

@agent_required
def agent_queue_view(request):
    events = RevenueEvent.objects.filter(status="escalated").select_related("customer", "diagnosis", "decision")

    cases = []
    for event in events:
        brief_log = event.audit_trail.filter(stage="action_attempted").order_by("-created_at").first()
        brief = brief_log.detail.get("brief", "") if brief_log else ""
        cases.append({"event": event, "brief": brief})

    return render(request, "audit/agent_queue.html", {"cases": cases})


@agent_required
def agent_resolve_view(request, event_id):
    from apps.audit.services import log_audit
    event = get_object_or_404(RevenueEvent, pk=event_id)
    if request.method == "POST":
        event.status = "recovered"
        event.recovered_amount = event.amount
        event.save(update_fields=["status", "recovered_amount", "updated_at"])
        log_audit(event, "agent_action", {"resolved_by": request.user.username})
    return redirect("agent-queue")