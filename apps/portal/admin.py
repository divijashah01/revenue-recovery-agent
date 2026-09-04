from django.contrib import admin
from .models import PortalLink


@admin.register(PortalLink)
class PortalLinkAdmin(admin.ModelAdmin):
    list_display = ("revenue_event", "token", "payment_link_url", "created_at")