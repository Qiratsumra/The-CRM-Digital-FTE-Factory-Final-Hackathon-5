"""Channel-aware response formatting."""
from enum import Enum


class Channel(str, Enum):
    """Supported communication channels."""
    EMAIL = "email"
    WEB_FORM = "web_form"
    WHATSAPP = "whatsapp"


def format_for_channel(content: str, channel: Channel, ticket_id: str = "") -> str:
    """
    Format response for the target channel.

    Args:
        content: Response content
        channel: Target channel
        ticket_id: Optional ticket reference

    Returns:
        Formatted response string
    """
    if channel == Channel.EMAIL:
        return (
            f"Dear Customer,\n\nThank you for reaching out to Qirat Saeed AI Support.\n\n"
            f"{content}\n\n"
            f"Best regards,\nQirat Saeed AI Support Team\n"
            f"---\nTicket: {ticket_id}"
        )
    elif channel == Channel.WHATSAPP:
        # WhatsApp has a 300 character limit
        truncated = content[:300]
        if len(content) > 300:
            truncated = truncated.rsplit(' ', 1)[0] + "..."  # Cut at word boundary
        return truncated
    else:  # web_form
        return f"{content}\n\n---\nNeed more help? Reply or contact support."


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def truncate_to_words(text: str, max_words: int) -> str:
    """Truncate text to maximum word count."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."
