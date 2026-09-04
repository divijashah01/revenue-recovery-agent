import uuid
from django.db import models
from apps.events.models import RevenueEvent


class PortalLink(models.Model):
    """One secure, unguessable link per event — this is the magic-link
    the customer receives instead of exposing internal event IDs."""
    revenue_event = models.OneToOneField(RevenueEvent, on_delete=models.CASCADE, related_name="portal_link")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment_link_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PortalLink for event {self.revenue_event_id}"