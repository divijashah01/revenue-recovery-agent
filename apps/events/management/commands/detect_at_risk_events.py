from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.events.models import CheckoutSession, Invoice, RevenueEvent

ABANDONMENT_THRESHOLD_MINUTES = 30


class Command(BaseCommand):
    """
    The actual 'detection' sweep for the two leak types that aren't
    webhook-driven: checkout abandonment (idle sessions) and overdue
    receivables (invoices past due). Idempotent — won't duplicate events
    for sessions/invoices already converted.
    """
    help = "Scans for newly abandoned checkouts and newly overdue invoices, creates RevenueEvents."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=ABANDONMENT_THRESHOLD_MINUTES)
        new_events = 0

        stale_sessions = CheckoutSession.objects.filter(status="active", last_activity_at__lt=cutoff)
        for session in stale_sessions:
            session.status = "abandoned"
            session.save(update_fields=["status"])
            RevenueEvent.objects.get_or_create(
                checkout_session=session,
                event_type="checkout_abandonment",
                defaults={
                    "customer": session.customer,
                    "amount": session.amount,
                    "source": "detector",
                },
            )
            new_events += 1

        today = timezone.now().date()
        newly_overdue = Invoice.objects.filter(status="pending", due_date__lt=today)
        for invoice in newly_overdue:
            invoice.status = "overdue"
            invoice.save(update_fields=["status"])
            RevenueEvent.objects.get_or_create(
                invoice=invoice,
                event_type="overdue_invoice",
                defaults={
                    "customer": invoice.customer,
                    "amount": invoice.amount,
                    "source": "detector",
                },
            )
            new_events += 1

        self.stdout.write(self.style.SUCCESS(f"Detector run complete. {new_events} new revenue-at-risk events."))