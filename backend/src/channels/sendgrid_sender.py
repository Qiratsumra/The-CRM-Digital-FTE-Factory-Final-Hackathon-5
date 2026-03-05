"""SendGrid email sender for Render deployment."""
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from src.config import get_settings
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()


class SendGridSender:
    """Send emails via SendGrid API."""

    def __init__(self) -> None:
        self.api_key = getattr(settings, 'sendgrid_api_key', None)
        self.from_email = getattr(settings, 'sendgrid_from_email', 'sheikhqirat100@gmail.com')

    async def send_ticket_response(
        self,
        to_email: str,
        ticket_id: str,
        subject: str,
        response: str,
        customer_name: Optional[str] = None,
    ) -> bool:
        """Send ticket response email via SendGrid."""

        if not self.api_key:
            logger.warning("SendGrid API key not configured")
            return False

        try:
            # Create email
            from_email = Email(self.from_email, "Qirat Saeed AI Support")
            to_email_obj = To(to_email)
            subject_line = f"Re: {subject} (Ticket #{ticket_id[:8]})"

            # Create HTML content
            html_content = self._create_html_response(
                ticket_id, subject, response, customer_name
            )

            content = Content("text/html", html_content)
            mail = Mail(from_email, to_email_obj, subject_line, content)

            # Send via SendGrid
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return False

    def _create_html_response(
        self,
        ticket_id: str,
        subject: str,
        response: str,
        customer_name: Optional[str],
    ) -> str:
        """Create HTML email template."""
        greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 24px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }}
        .content {{
            background: white;
            padding: 32px;
            border: 1px solid #e5e7eb;
            border-top: none;
        }}
        .ticket-info {{
            background: #f3f4f6;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
        }}
        .response {{
            background: #f9fafb;
            padding: 20px;
            border-left: 4px solid #1f2937;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .footer {{
            background: #f9fafb;
            padding: 24px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
            border: 1px solid #e5e7eb;
            border-top: none;
            border-radius: 0 0 12px 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Qirat Saeed AI Support</h1>
    </div>

    <div class="content">
        <p>{greeting}</p>

        <p>Thank you for contacting Qirat Saeed AI Support. We've reviewed your inquiry and here's our response:</p>

        <div class="ticket-info">
            <strong>Ticket ID:</strong> {ticket_id}<br>
            <strong>Subject:</strong> {subject}<br>
            <strong>Status:</strong> <span style="color: #059669;">✓ Resolved by AI</span>
        </div>

        <div class="response">
            {response.replace(chr(10), '<br>')}
        </div>

        <p>Was this response helpful? If you need further assistance, please reply to this email.</p>

        <p style="margin-top: 24px;">
            Best regards,<br>
            <strong>Qirat Saeed AI Support Team</strong>
        </p>
    </div>

    <div class="footer">
        <p>This is an automated response from our AI support agent.</p>
        <p style="margin-top: 12px; font-size: 12px;">
            © 2026 Qirat Saeed. All rights reserved.
        </p>
    </div>
</body>
</html>
"""


# Singleton instance
_sendgrid_sender: Optional[SendGridSender] = None


def get_sendgrid_sender() -> SendGridSender:
    """Get or create SendGrid sender instance."""
    global _sendgrid_sender
    if _sendgrid_sender is None:
        _sendgrid_sender = SendGridSender()
    return _sendgrid_sender
