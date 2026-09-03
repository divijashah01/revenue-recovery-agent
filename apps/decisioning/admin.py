from django.contrib import admin
from .models import InterventionRule, Decision, InterventionAttempt


@admin.register(InterventionRule)
class InterventionRuleAdmin(admin.ModelAdmin):
    list_display = ("root_cause", "action", "base_recovery_probability", "notes")
    list_filter = ("root_cause", "action")


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ("revenue_event", "chosen_action", "expected_value", "expected_recovery_probability", "reason", "decided_at")
    list_filter = ("chosen_action", "reason")
    readonly_fields = ("candidates_considered",)


@admin.register(InterventionAttempt)
class InterventionAttemptAdmin(admin.ModelAdmin):
    list_display = ("revenue_event", "action", "outcome", "attempted_at")
    list_filter = ("action", "outcome")