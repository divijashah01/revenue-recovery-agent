from .base import ChannelResult
from myproject.intervention_costs import SMS_TRANSACTIONAL_COST


def send_sms_reminder(to_phone, message):
    """
    Mocked send — no live SMS provider wired up (deliberate scope decision;
    see README > Research Notes). Cost is still logged at the real MSG91
    published rate so batch-level cost/ROI reporting stays accurate even
    though delivery isn't live.
    """
    print(f"[MOCK SMS] to {to_phone}: {message}")
    return ChannelResult(success=True, detail="mock_sent", cost=SMS_TRANSACTIONAL_COST)