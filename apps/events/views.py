import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status as http_status

from .models import Customer, RevenueEvent
from .services import process_event_immediately


class RazorpayWebhookView(APIView):
    """
    Real Razorpay webhook receiver (test mode). Verifies signature, handles
    payment.failed events, and normalizes them into a RevenueEvent — this is
    the actual detection entry point for the payment_failure leak type.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_webhook_signature(
                payload.decode("utf-8"),
                signature,
                settings.RAZORPAY_WEBHOOK_SECRET,
            )
        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "invalid signature"}, status=http_status.HTTP_400_BAD_REQUEST)

        data = request.data
        webhook_event_name = data.get("event")

        if webhook_event_name == "payment.failed":
            payment_entity = data["payload"]["payment"]["entity"]

            notes = payment_entity.get("notes")
            notes = notes if isinstance(notes, dict) else {}

            customer, _ = Customer.objects.get_or_create(
                phone=payment_entity.get("contact", ""),
                defaults={
                    "name": notes.get("name", "Unknown Customer"),
                    "email": payment_entity.get("email", ""),
                },
            )

            revenue_event = RevenueEvent.objects.create(
                event_type="payment_failure",
                customer=customer,
                amount=payment_entity.get("amount", 0) / 100,
                currency=payment_entity.get("currency", "INR"),
                source="razorpay",
                error_code=payment_entity.get("error_code", ""),
                error_reason=payment_entity.get("error_reason", ""),
                raw_payload=data,
            )
            process_event_immediately(revenue_event)

        return Response({"status": "ok"}, status=http_status.HTTP_200_OK)