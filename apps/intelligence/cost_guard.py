from myproject.intervention_costs import GEMINI_FLASH_LITE_COST_PER_CALL


def llm_worth_it(revenue_event):
    """
    Guards LLM spend against the ROI optimizer's own math. If the event's
    expected recovery value doesn't clear even the LLM's small per-call
    cost, skip Gemini and use the static fallback — the AI layer respects
    the same cost discipline as the money-decision layer, not a special
    exemption from it.
    """
    decision = getattr(revenue_event, "decision", None)
    if not decision or decision.expected_value is None:
        return True  # no decision yet (e.g. diagnosis stage) — default allow
    return float(decision.expected_value) > GEMINI_FLASH_LITE_COST_PER_CALL