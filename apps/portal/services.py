from django.conf import settings
from .models import PortalLink


def get_or_create_portal_link(revenue_event):
    link, _ = PortalLink.objects.get_or_create(revenue_event=revenue_event)
    return link


def portal_url(link):
    return f"{settings.SITE_BASE_URL}/portal/{link.token}/"