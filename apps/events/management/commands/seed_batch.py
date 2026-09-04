import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.events.models import Customer, CheckoutSession, Invoice, RevenueEvent

fake = Faker("en_IN")

# Real Razorpay failure reasons (from Razorpay's documented error-reason taxonomy)
PAYMENT_FAILURE_REASONS = [
    ("BAD_REQUEST_ERROR", "insufficient_funds"),
    ("BAD_REQUEST_ERROR", "card_declined"),
    ("BAD_REQUEST_ERROR", "incorrect_cvv"),
    ("BAD_REQUEST_ERROR", "authentication_failed"),
    ("GATEWAY_ERROR", "bank_technical_error"),
    ("GATEWAY_ERROR", "bank_not_available"),
    ("BAD_REQUEST_ERROR", "payment_failed"),
]


class Command(BaseCommand):
    help = "Seeds a realistic demo batch: payment failures, abandoned checkouts, overdue invoices."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=50)

    def handle(self, *args, **options):
        count = options["count"]
        created = 0

        for _ in range(count):
            customer = Customer.objects.create(
                name=fake.name(),
                phone=f"+91{fake.msisdn()[3:]}",
                email=fake.email(),
                language_preference=random.choices(["en", "hi-en"], weights=[0.7, 0.3])[0],
            )

            leak_type = random.choices(
                ["payment_failure", "checkout_abandonment", "overdue_invoice"],
                weights=[0.45, 0.35, 0.20],
            )[0]

            if leak_type == "payment_failure":
                error_code, error_reason = random.choice(PAYMENT_FAILURE_REASONS)
                RevenueEvent.objects.create(
                    event_type="payment_failure",
                    customer=customer,
                    amount=round(random.uniform(299, 15000), 2),
                    source="seed",
                    error_code=error_code,
                    error_reason=error_reason,
                    raw_payload={"seeded": True},
                )

            elif leak_type == "checkout_abandonment":
                session = CheckoutSession.objects.create(
                    customer=customer,
                    cart_reference=f"CART-{fake.uuid4()[:8]}",
                    amount=round(random.uniform(199, 8000), 2),
                    stage=random.choice(["cart", "shipping", "payment", "review"]),
                    status="abandoned",
                )
                # backdate last_activity to simulate a real abandoned session
                CheckoutSession.objects.filter(pk=session.pk).update(
                    last_activity_at=timezone.now() - timedelta(minutes=random.randint(31, 500))
                )
                RevenueEvent.objects.create(
                    event_type="checkout_abandonment",
                    customer=customer,
                    amount=session.amount,
                    source="seed",
                    checkout_session=session,
                    raw_payload={"seeded": True},
                )

            else:
                due_date = timezone.now().date() - timedelta(days=random.randint(1, 60))
                invoice = Invoice.objects.create(
                    customer=customer,
                    invoice_number=f"INV-{fake.uuid4()[:8].upper()}",
                    amount=round(random.uniform(5000, 200000), 2),
                    due_date=due_date,
                    status="overdue",
                )
                RevenueEvent.objects.create(
                    event_type="overdue_invoice",
                    customer=customer,
                    amount=invoice.amount,
                    source="seed",
                    invoice=invoice,
                    raw_payload={"seeded": True},
                )

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} revenue-at-risk events."))