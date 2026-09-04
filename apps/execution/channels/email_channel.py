from django.core.mail import send_mail
from django.conf import settings
from .base import ChannelResult


def send_email_reminder(to_email, subject, message):
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)
        return ChannelResult(success=True, detail="sent", cost=0.0)
    except Exception as e:
        return ChannelResult(success=False, detail=str(e), cost=0.0)