from django.db import models
from apps.events.models import RevenueEvent


class AuditEvent(models.Model):
    """
    Append-only log of every stage a RevenueEvent passes through. This is
    the audit trail the brief explicitly asks for — every recovered rupee
    should be traceable back to exactly why the agent did what it did.
    """
    STAGE_CHOICES = [
        ("diagnosed", "Diagnosed"),
        ("decided", "Decided"),
        ("action_attempted", "Action Attempted"),
        ("outcome_recorded", "Outcome Recorded"),
    ]

    revenue_event = models.ForeignKey(RevenueEvent, on_delete=models.CASCADE, related_name="audit_trail")
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES)
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Event {self.revenue_event_id} - {self.stage} @ {self.created_at}"