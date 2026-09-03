from django.contrib import admin
from .models import Diagnosis


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("revenue_event", "root_cause", "confidence", "diagnosed_at")
    list_filter = ("root_cause",)