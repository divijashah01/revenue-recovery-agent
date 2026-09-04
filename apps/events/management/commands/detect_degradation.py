from django.core.management.base import BaseCommand
from apps.events.models import Customer, RevenueEvent, PaymentAttemptLog
from apps.intelligence.risk_scoring import compute_degradation_risk

RISK_THRESHOLD = 0.4


class Command(BaseCommand):
    """
    The predictive detection sweep. Scans payment telemetry for customers
    showing degradation risk and flags them as revenue-at-risk BEFORE a
    hard failure occurs — this is the proactive counterpart to
    detect_at_risk_events.py, which only reacts to failures already happened.
    """
    help = "Scans payment telemetry for degradation risk, creates payment_degradation RevenueEvents."

    def handle(self, *args, **options):
        customer_ids = PaymentAttemptLog.objects.values_list("customer_id", flat=True).distinct()
        new_events = 0

        for customer_id in customer_ids:
            already_flagged = RevenueEvent.objects.filter(
                customer_id=customer_id, event_type="payment_degradation"
            ).exists()
            if already_flagged:
                continue

            customer = Customer.objects.get(pk=customer_id)
            score, signals = compute_degradation_risk(customer)

            if score >= RISK_THRESHOLD:
                latest_attempt = PaymentAttemptLog.objects.filter(customer=customer).order_by("-created_at").first()
                RevenueEvent.objects.create(
                    event_type="payment_degradation",
                    customer=customer,
                    amount=latest_attempt.amount,
                    source="detector",
                    raw_payload={"risk_score": score, "signals": signals},
                )
                new_events += 1

        self.stdout.write(self.style.SUCCESS(
            f"Degradation scan complete. {new_events} at-risk events flagged before hard failure."
        ))