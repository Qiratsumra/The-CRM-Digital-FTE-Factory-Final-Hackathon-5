"""
Skill: Channel Adaptation
When to use: BEFORE sending any response
Purpose: Format response appropriately for the target channel
"""
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Channel(str, Enum):
    """Supported communication channels."""
    EMAIL = "email"
    WEB_FORM = "web_form"


def adapt_response(response: str, channel: Channel, ticket_id: str = "") -> str:
    """
    Format response for the target channel.
    
    Args:
        response: Raw response text
        channel: Target channel
        ticket_id: Optional ticket ID for reference
        
    Returns:
        Channel-formatted response
    """
    if channel == Channel.EMAIL:
        return (
            f"Dear Customer,\n\nThank you for reaching out to NovaSaaS Support.\n\n"
            f"{response}\n\n"
            f"Best regards,\nNovaSaaS AI Support Team\n"
            f"---\nTicket: {ticket_id}"
        )
    else:  # web_form
        return f"{response}\n\n---\nNeed more help? Reply or visit support.novasaas.com"


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def truncate_to_words(text: str, max_words: int) -> str:
    """Truncate text to maximum word count."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."
