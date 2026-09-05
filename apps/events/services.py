from apps.diagnosis.classifiers import diagnose
from apps.decisioning.optimizer import decide
from apps.execution.executor import execute_decision


def process_event_immediately(revenue_event):
    """
    Runs the full detect->diagnose->decide->execute chain synchronously for
    ONE event, right in the request cycle. Deliberate scope decision: real
    production traffic should push this to a background worker to keep
    webhook response times low, but for a single live event this completes
    in a few seconds and lets the dashboard update instantly during a demo
    — worth the trade-off here, documented rather than hidden.
    """
    diagnosis = diagnose(revenue_event)
    decision = decide(revenue_event, diagnosis)
    if decision:
        execute_decision(revenue_event)
    return revenue_event