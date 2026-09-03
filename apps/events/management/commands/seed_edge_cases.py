from django.utils import timezone
from datetime import timedelta
from django.core.management.base import BaseCommand
from apps.events.models import Customer, CheckoutSession, Invoice, RevenueEvent


class Command(BaseCommand):
    """
    Deliberately seeds a handful of low-value / edge-case events. These exist
    specifically to demonstrate the ROI optimizer refusing to chase amounts
    where every available action's expected value is negative, and to show
    a compliance-driven stop (opted-out customer) alongside a value-driven
    one. Kept separate from seed_batch.py so the main batch's distribution
    stays representative and this set stays clearly labeled as a demo case.
    """
    help = "Seeds a small set of edge-case events to exercise the 'stop' pathway."

    def handle(self, *args, **options):
        # Case 1: tiny payment failures — cost of any action exceeds recoverable value
        for amount in [8, 15, 25, 35]:
            customer = Customer.objects.create(
                name=f"Edge Case Customer ₹{amount}",
                phone=f"+91900000{amount:04d}",
                email=f"edge{amount}@example.com",
            )
            RevenueEvent.objects.create(
                event_type="payment_failure",
                customer=customer,
                amount=amount,
                source="seed",
                error_code="BAD_REQUEST_ERROR",
                error_reason="payment_failed",
                raw_payload={"seeded": True, "edge_case": "low_value_payment_failure"},
            )

        # Case 2: tiny overdue invoice — even human escalation cost (₹20) exceeds it
        customer = Customer.objects.create(
            name="Edge Case Customer - Tiny Invoice",
            phone="+919000009999",
            email="edgeinvoice@example.com",
        )
        invoice = Invoice.objects.create(
            customer=customer,
            invoice_number="INV-EDGE001",
            amount=12,
            due_date=timezone.now().date() - timedelta(days=45),
            status="overdue",
        )
        RevenueEvent.objects.create(
            event_type="overdue_invoice",
            customer=customer,
            amount=invoice.amount,
            source="seed",
            invoice=invoice,
            raw_payload={"seeded": True, "edge_case": "low_value_invoice"},
        )

        # Case 3: opted-out customer — compliance stop, not ROI stop
        opted_out_customer = Customer.objects.create(
            name="Edge Case Customer - Opted Out",
            phone="+919000008888",
            email="optedout@example.com",
            opted_out=True,
        )
        RevenueEvent.objects.create(
            event_type="payment_failure",
            customer=opted_out_customer,
            amount=2500,
            source="seed",
            error_code="BAD_REQUEST_ERROR",
            error_reason="card_declined",
            raw_payload={"seeded": True, "edge_case": "opted_out_customer"},
        )

        self.stdout.write(self.style.SUCCESS("Seeded edge-case events for stop-pathway demo."))