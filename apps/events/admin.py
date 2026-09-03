from django.contrib import admin
from .models import Customer, CheckoutSession, Invoice, RevenueEvent


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")


@admin.register(CheckoutSession)
class CheckoutSessionAdmin(admin.ModelAdmin):
    list_display = ("cart_reference", "customer", "amount", "stage", "status", "last_activity_at")
    list_filter = ("stage", "status")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "amount", "due_date", "status")
    list_filter = ("status",)


@admin.register(RevenueEvent)
class RevenueEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "customer", "amount", "status", "source", "error_reason", "detected_at")
    list_filter = ("event_type", "status", "source")
    readonly_fields = ("raw_payload", "detected_at", "updated_at")