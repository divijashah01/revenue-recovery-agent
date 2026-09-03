from django.db import models
from apps.events.models import RevenueEvent
from apps.diagnosis.models import Diagnosis

ACTION_CHOICES = [
    ("retry_payment", "Retry Payment"),
    ("send_payment_link", "Send Fresh Payment Link"),
    ("whatsapp_nudge", "WhatsApp Nudge"),
    ("email_reminder", "Email Reminder"),
    ("sms_reminder", "SMS Reminder"),
    ("promise_to_pay", "Promise-to-Pay Request"),
    ("escalate_human", "Escalate to Human Agent"),
    ("stop", "Stop — No Further Action"),
]


class InterventionRule(models.Model):
    """
    Admin-editable root_cause -> candidate action mapping, with a base
    recovery-probability estimate. This is what makes the action set
    'bounded' — the optimizer can only ever pick from rows that exist here.
    """
    root_cause = models.CharField(max_length=50)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    base_recovery_probability = models.FloatField()  # 0.0–1.0, seeded assumption, refined from Outcomes
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("root_cause", "action")

    def __str__(self):
        return f"{self.root_cause} -> {self.action} (p={self.base_recovery_probability})"


class Decision(models.Model):
    """
    One decision per event. candidates_considered stores every action that
    was scored (not just the winner) — this is the explainability record
    judges/auditors can inspect: 'why this action and not another'.
    """
    revenue_event = models.OneToOneField(RevenueEvent, on_delete=models.CASCADE, related_name="decision")
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE)
    chosen_action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    expected_recovery_probability = models.FloatField(null=True, blank=True)
    expected_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expected_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    candidates_considered = models.JSONField(default=list)
    reason = models.CharField(max_length=255, blank=True)  # e.g. "max_attempts_reached", "best_expected_value"
    decided_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.revenue_event} -> {self.chosen_action}"


class InterventionAttempt(models.Model):
    """
    Every attempted action against an event, used by the stopping-rule
    guards to enforce max-attempts and cooldown windows. Execution (Phase 4)
    will update `outcome` once a channel actually fires.
    """
    OUTCOME_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ]

    revenue_event = models.ForeignKey(RevenueEvent, on_delete=models.CASCADE, related_name="attempts")
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default="pending")
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.revenue_event} - {self.action} ({self.outcome})"