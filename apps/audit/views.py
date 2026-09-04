from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count
from django.core.paginator import Paginator

from apps.events.models import RevenueEvent
from apps.decisioning.models import Decision


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