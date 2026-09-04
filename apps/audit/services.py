from .models import AuditEvent


def log_audit(revenue_event, stage, detail=None):
    AuditEvent.objects.create(revenue_event=revenue_event, stage=stage, detail=detail or {})