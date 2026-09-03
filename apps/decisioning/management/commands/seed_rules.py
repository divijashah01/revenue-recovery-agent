from django.core.management.base import BaseCommand
from apps.decisioning.models import InterventionRule
from apps.decisioning.rules_seed_data import RULES


class Command(BaseCommand):
    help = "Seeds the InterventionRule table from rules_seed_data.py"

    def handle(self, *args, **options):
        created = 0
        for root_cause, action, probability, notes in RULES:
            _, was_created = InterventionRule.objects.update_or_create(
                root_cause=root_cause,
                action=action,
                defaults={"base_recovery_probability": probability, "notes": notes},
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded/updated {len(RULES)} rules ({created} newly created)."))