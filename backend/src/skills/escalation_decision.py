"""
Skill: Escalation Decision
When to use: After generating response, before sending
Purpose: Determine if conversation requires human escalation
"""
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

HARD_ESCALATION_KEYWORDS = [
    "lawyer", "legal", "sue", "attorney", "lawsuit",
    "refund", "cancellation", "cancel", "chargeback",
    "gdpr", "data breach", "compliance",
]

HUMAN_REQUEST_KEYWORDS = ["human", "agent", "real person", "manager", "representative"]


@dataclass
class EscalationDecision:
    """Escalation decision result."""
    should_escalate: bool
    reason: str
    urgency: str  # "immediate" | "high" | "normal"


def decide_escalation(message: str, sentiment_score: float) -> EscalationDecision:
    """
    Decide if message requires escalation based on rules and sentiment.
    
    Args:
        message: Customer message text
        sentiment_score: Sentiment score 0.0-1.0
        
    Returns:
        EscalationDecision with flag, reason, and urgency
    """
    message_lower = message.lower()

    # Check hard escalation keywords
    for kw in HARD_ESCALATION_KEYWORDS:
        if kw in message_lower:
            return EscalationDecision(
                should_escalate=True,
                reason=f"keyword_detected:{kw}",
                urgency="immediate",
            )

    # Check human request keywords
    for kw in HUMAN_REQUEST_KEYWORDS:
        if re.search(rf"\b{kw}\b", message_lower):
            return EscalationDecision(
                should_escalate=True,
                reason="customer_requested_human",
                urgency="high",
            )

    # Check sentiment thresholds
    if sentiment_score < 0.2:
        return EscalationDecision(
            should_escalate=True,
            reason="hostile_sentiment",
            urgency="immediate",
        )

    if sentiment_score < 0.3:
        return EscalationDecision(
            should_escalate=True,
            reason="negative_sentiment",
            urgency="high",
        )

    return EscalationDecision(should_escalate=False, reason="", urgency="normal")
