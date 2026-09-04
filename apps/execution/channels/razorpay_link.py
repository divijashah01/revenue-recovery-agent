import razorpay
from django.conf import settings


def create_payment_link(customer, amount):
    """
    Real Razorpay Payment Links API call (test mode) — unlike WhatsApp,
    this needs no template approval, so it's genuinely live immediately.
    """
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        link = client.payment_link.create({
            "amount": int(float(amount) * 100),
            "currency": "INR",
            "description": "Complete your payment",
            "customer": {
                "name": customer.name,
                "email": customer.email or "test@example.com",
                "contact": customer.phone or "+919999999999",
            },
            "notify": {"sms": False, "email": False},
            "reminder_enable": False,
        })
        return link.get("short_url")
    except Exception as e:
        print(f"[Razorpay Payment Link] failed: {e}")
        return None