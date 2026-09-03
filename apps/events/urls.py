from django.urls import path
from .views import RazorpayWebhookView

urlpatterns = [
    path("webhooks/razorpay/", RazorpayWebhookView.as_view(), name="razorpay-webhook"),
]