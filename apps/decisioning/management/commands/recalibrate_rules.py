from django.core.management.base import BaseCommand
from apps.decisioning.adaptive_learning import recalibrate_probabilities


class Command(BaseCommand):
    help = "Recalibrates InterventionRule probabilities from observed batch outcomes."

    def handle(self, *args, **options):
        changes = recalibrate_probabilities()
        if not changes:
            self.stdout.write("No rules had enough observations to recalibrate yet.")
            return

        for root_cause, action, prior, posterior, total, successes in changes:
            self.stdout.write(
                f"{root_cause} -> {action}: {prior} -> {posterior}  ({successes}/{total} observed)"
            )
        self.stdout.write(self.style.SUCCESS(f"Recalibrated {len(changes)} rules."))