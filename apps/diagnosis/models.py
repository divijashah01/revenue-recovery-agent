from django.db import models
from apps.events.models import RevenueEvent


class Diagnosis(models.Model):
    """
    One diagnosis per event. Root cause is a short machine-readable code
    used directly by the decisioning rule table — this is the join key
    between 'why it happened' and 'what to do about it'.
    """
    revenue_event = models.OneToOneField(RevenueEvent, on_delete=models.CASCADE, related_name="diagnosis")
    root_cause = models.CharField(max_length=50)
    explanation = models.CharField(max_length=255)
    confidence = models.FloatField(default=1.0)  # 1.0 = direct mapping, lower = inferred
    diagnosed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.revenue_event} -> {self.root_cause}"