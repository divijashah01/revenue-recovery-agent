import random
from django.core.management.base import BaseCommand
from apps.events.models import RevenueEvent
from apps.audit.services import log_audit


class Command(BaseCommand):
    """
    DEMO-ONLY simulation of whether an intervention actually recovered the
    money, weighted by the decision's own expected recovery probability.
    Stands in for a real payment.captured webhook / invoice-paid signal,
    which can't be observed synchronously in a hackathon timeframe. This
    is documented as simulated in the README — not represented as real.
    """
    help = "Simulates recovery confirmation for in-progress events, weighted by expected probability."

    def handle(self, *args, **options):
        events = RevenueEvent.objects.filter(status="in_progress").select_related("decision")
        recovered_count = 0

        for event in events:
            decision = getattr(event, "decision", None)
            probability = float(decision.expected_recovery_probability) if decision and decision.expected_recovery_probability else 0.1

            if random.random() < probability:
                event.status = "recovered"
                event.recovered_amount = event.amount
                event.save(update_fields=["status", "recovered_amount", "updated_at"])
                log_audit(event, "outcome_recorded", {"recovered": True, "amount": str(event.amount)})
                recovered_count += 1
            else:
                log_audit(event, "outcome_recorded", {"recovered": False})

        self.stdout.write(self.style.SUCCESS(f"Simulated outcomes for {events.count()} events, {recovered_count} recovered."))