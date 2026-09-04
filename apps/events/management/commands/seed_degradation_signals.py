import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from apps.events.models import Customer, PaymentAttemptLog

fake = Faker("en_IN")


class Command(BaseCommand):
    """
    Seeds customers showing a degrading payment pattern (rising soft
    declines, worsening latency) that has NOT yet produced a hard failure.
    This is the raw material the degradation detector reads to flag
    at-risk revenue before it's actually lost.
    """
    help = "Seeds payment attempt telemetry showing pre-failure degradation."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=15)

    def handle(self, *args, **options):
        created = 0
        for _ in range(options["count"]):
            customer = Customer.objects.create(
                name=fake.name(),
                phone=f"+91{fake.msisdn()[3:]}",
                email=fake.email(),
            )
            amount = round(random.uniform(500, 20000), 2)
            attempt_count = random.randint(2, 4)
            base_latency = random.randint(800, 1500)

            for i in range(attempt_count):
                is_last = i == attempt_count - 1
                status = "soft_decline" if not is_last or random.random() > 0.3 else "hard_decline"
                latency = base_latency + (i * random.randint(300, 800))  # worsening each attempt

                log = PaymentAttemptLog.objects.create(
                    customer=customer,
                    amount=amount,
                    attempt_number=i + 1,
                    status=status,
                    latency_ms=latency,
                )
                PaymentAttemptLog.objects.filter(pk=log.pk).update(
                    created_at=timezone.now() - timedelta(minutes=(attempt_count - i) * 8)
                )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded degradation telemetry for {created} customers."))