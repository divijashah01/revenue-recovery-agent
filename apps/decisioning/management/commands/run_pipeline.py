from django.core.management.base import BaseCommand
from apps.events.models import RevenueEvent
from apps.diagnosis.classifiers import diagnose
from apps.decisioning.optimizer import decide


class Command(BaseCommand):
    """
    Orchestrates diagnosis + decisioning for every event still in 'detected'
    state. This is the pipeline you'll run before Phase 4 execution picks
    up 'decided' events and actually fires the channels.
    """
    help = "Runs diagnosis + decision engine over all detected RevenueEvents."

    def handle(self, *args, **options):
        events = RevenueEvent.objects.filter(status="detected")
        diagnosed_count = 0
        decided_count = 0

        for event in events:
            diagnosis = diagnose(event)
            diagnosed_count += 1

            decision = decide(event, diagnosis)
            if decision:
                decided_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Diagnosed {diagnosed_count} events, decided {decided_count} events."
        ))