from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)   # E.164 format, used for WhatsApp
    email = models.EmailField(blank=True)
    opted_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone or self.email})"


class CheckoutSession(models.Model):
    STAGE_CHOICES = [
        ("cart", "Cart"),
        ("shipping", "Shipping Details"),
        ("payment", "Payment Step"),
        ("review", "Review / Confirm"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("abandoned", "Abandoned"),
        ("recovered", "Recovered"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    cart_reference = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="cart")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Checkout {self.cart_reference} - {self.status}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("overdue", "Overdue"),
        ("paid", "Paid"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.status}"


class RevenueEvent(models.Model):
    """
    The single normalized entry point for every leak type this agent handles.
    Diagnosis, decisioning, and execution all key off this model — this is
    what makes the three problem types (payment failure, abandonment,
    overdue invoice) flow through one uniform pipeline.
    """

    EVENT_TYPE_CHOICES = [
        ("payment_failure", "Payment Failure"),
        ("checkout_abandonment", "Checkout Abandonment"),
        ("overdue_invoice", "Overdue Invoice"),
        ("payment_degradation", "Payment Degradation (Predictive)"),
    ]
    SOURCE_CHOICES = [
        ("razorpay", "Razorpay Webhook"),
        ("seed", "Seeded Demo Data"),
        ("detector", "Internal Detector Job"),
    ]
    STATUS_CHOICES = [
        ("detected", "Detected"),
        ("diagnosed", "Diagnosed"),
        ("decided", "Decided"),
        ("in_progress", "Intervention In Progress"),
        ("recovered", "Recovered"),
        ("stopped", "Stopped"),
        ("escalated", "Escalated to Human"),
    ]

    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="detected")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="seed")

    # Links back to the originating record, only one will be set depending on event_type
    checkout_session = models.ForeignKey(CheckoutSession, null=True, blank=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL)

    # Populated for payment_failure events, using Razorpay's actual error taxonomy
    error_code = models.CharField(max_length=100, blank=True)     # e.g. BAD_REQUEST_ERROR
    error_reason = models.CharField(max_length=100, blank=True)   # e.g. insufficient_funds

    raw_payload = models.JSONField(null=True, blank=True)

    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.event_type}] ₹{self.amount} - {self.customer} ({self.status})"

class PaymentAttemptLog(models.Model):
    """
    Raw, low-level payment attempt telemetry — separate from RevenueEvent.
    This is what a real gateway integration would stream continuously.
    Multiple soft-decline attempts here, before any hard failure, are what
    the degradation detector reads to flag risk *before* revenue is lost —
    this is the 'detects revenue at risk' pathway, not just reactive cleanup.
    """
    STATUS_CHOICES = [
        ("success", "Success"),
        ("soft_decline", "Soft Decline / Retry Needed"),
        ("hard_decline", "Hard Decline"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} attempt #{self.attempt_number} - {self.status}"