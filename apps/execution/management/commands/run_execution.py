from django.core.management.base import BaseCommand
from apps.events.models import RevenueEvent
from apps.execution.executor import execute_decision


class Command(BaseCommand):
    help = "Executes chosen actions for every RevenueEvent currently in 'decided' state."

    def handle(self, *args, **options):
        events = RevenueEvent.objects.filter(status="decided")
        executed = 0
        for event in events:
            attempt = execute_decision(event)
            if attempt:
                executed += 1
        self.stdout.write(self.style.SUCCESS(f"Executed {executed} interventions."))