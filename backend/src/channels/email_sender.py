"""Email sender service for sending responses via Gmail."""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import get_settings
from typing import Optional

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailSender:
    """Send emails via Gmail SMTP."""

    def __init__(self) -> None:
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = getattr(settings, 'gmail_sender_email', None)
        self.sender_password = getattr(settings, 'gmail_sender_password', None)

    async def send_ticket_response(
        self,
        to_email: str,
        ticket_id: str,
        subject: str,
        response: str,
        customer_name: Optional[str] = None,
    ) -> bool:
        """
        Send ticket response email to customer.

        Args:
            to_email: Customer email address
            ticket_id: Ticket UUID
            subject: Original ticket subject
            response: AI-generated response
            customer_name: Customer name (optional)

        Returns:
            True if sent successfully
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("Gmail credentials not configured. Email not sent.")
            # Store in DB anyway
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Re: {subject} (Ticket #{ticket_id[:8]})"
            msg["From"] = self.sender_email
            msg["To"] = to_email

            # Create HTML version
            html = self._create_html_response(
                ticket_id, subject, response, customer_name
            )

            # Attach HTML
            msg.attach(MIMEText(html, "html", "utf-8"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email} for ticket {ticket_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
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
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
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
            font-size: 14px;
        }}
        .ticket-info strong {{
            color: #1f2937;
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
        .button {{
            display: inline-block;
            background: #1f2937;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 8px;
            margin-top: 16px;
            font-weight: 500;
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
        
        <p>Was this response helpful? If you need further assistance, please reply to this email or submit a new ticket.</p>
        
        <p style="margin-top: 24px;">
            Best regards,<br>
            <strong>Qirat Saeed AI Support Team</strong>
        </p>
    </div>

    <div class="footer">
        <p>This is an automated response from our AI support agent.</p>
        <p>
            <a href="#" style="color: #6b7280; text-decoration: underline;">View Ticket Status</a> • 
            <a href="#" style="color: #6b7280; text-decoration: underline;">Submit New Ticket</a>
        </p>
        <p style="margin-top: 12px; font-size: 12px;">
            © 2026 Qirat Saeed. All rights reserved.
        </p>
    </div>
</body>
</html>
"""

    async def send_escalation_notification(
        self,
        ticket_id: str,
        customer_email: str,
        reason: str,
        channel: str,
        message_history: str,
    ) -> bool:
        """
        Send escalation notification to support team.

        Args:
            ticket_id: Ticket UUID
            customer_email: Customer email
            reason: Escalation reason
            channel: Support channel
            message_history: Full conversation history

        Returns:
            True if sent successfully
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("Gmail credentials not configured. Escalation email not sent.")
            return False

        # Support team email (configure in .env)
        support_email = getattr(settings, 'support_team_email', 'sheikhqirat100@gmail.com')

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 ESCALATED: Ticket #{ticket_id[:8]}"
            msg["From"] = self.sender_email
            msg["To"] = support_email

            html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc2626; color: white; padding: 20px; border-radius: 8px; }}
        .content {{ padding: 20px; background: #f9fafb; }}
        .info {{ background: white; padding: 16px; border-radius: 8px; margin: 16px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 Ticket Escalated</h2>
    </div>
    <div class="content">
        <div class="info">
            <strong>Ticket ID:</strong> {ticket_id}<br>
            <strong>Customer:</strong> {customer_email}<br>
            <strong>Channel:</strong> {channel}<br>
            <strong>Reason:</strong> {reason}
        </div>
        <h3>Message History:</h3>
        <pre style="background: white; padding: 16px; border-radius: 8px; overflow-x: auto;">{message_history}</pre>
        <p><a href="#" style="color: #2563eb;">View in Dashboard →</a></p>
    </div>
</body>
</html>
"""

            msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, support_email, msg.as_string())

            logger.info(f"Escalation notification sent to {support_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send escalation notification: {e}")
            return False


# Singleton instance
_email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """Get or create email sender instance."""
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSender()
    return _email_sender
