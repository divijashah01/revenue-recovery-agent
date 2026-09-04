from apps.events.models import PaymentAttemptLog


def compute_degradation_risk(customer):
    """
    Deterministic, auditable composite risk score from recent payment
    telemetry. Kept fully transparent (no LLM here) so the risk number
    itself is always explainable — Gemini reasoning is layered on top of
    this score at diagnosis time, only for the ambiguous middle band.
    """
    recent = list(PaymentAttemptLog.objects.filter(customer=customer).order_by("-created_at")[:5])
    if not recent:
        return 0.0, {}

    soft_decline_count = sum(1 for a in recent if a.status == "soft_decline")
    hard_decline_count = sum(1 for a in recent if a.status == "hard_decline")
    latencies = [a.latency_ms for a in reversed(recent)]  # oldest -> newest
    latency_trend = latencies[-1] - latencies[0] if len(latencies) > 1 else 0

    score = (soft_decline_count * 0.2) + (hard_decline_count * 0.35) + (0.15 if latency_trend > 500 else 0)
    score = round(min(score, 1.0), 2)

    signals = {
        "soft_decline_count": soft_decline_count,
        "hard_decline_count": hard_decline_count,
        "latency_trend_ms": latency_trend,
        "attempts_considered": len(recent),
    }
    return score, signals