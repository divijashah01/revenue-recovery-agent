from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("revenue_event", "stage", "created_at")
    list_filter = ("stage",)
    readonly_fields = ("revenue_event", "stage", "detail", "created_at")

    def has_add_permission(self, request):
        return False  # append-only — no manual creation via admin

    def has_change_permission(self, request, obj=None):
        return False  # immutable