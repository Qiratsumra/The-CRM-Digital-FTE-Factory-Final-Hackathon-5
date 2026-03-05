"""Gmail channel handler for incoming/outgoing emails."""
from src.database.connection import get_pool
from src.kafka.client import FTEKafkaProducer
from src.kafka.topics import TOPICS
from src.config import get_settings
import logging
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import BytesParser
from email.policy import default
from typing import Optional, List, Dict, Any
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)
settings = get_settings()


class GmailHandler:
    """Handle Gmail webhook notifications and send replies."""

    def __init__(self, producer: FTEKafkaProducer) -> None:
        self._producer = producer
        self._service: Optional[Any] = None
        self._credentials: Optional[Any] = None

    def _get_gmail_service(self) -> Any:
        """Get authenticated Gmail API service."""
        if self._service is not None:
            return self._service

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            import json
            import os

            # Try from environment variable first (for Render)
            creds_json = os.getenv("GMAIL_CREDENTIALS_FILE")
            if creds_json:
                try:
                    credentials = service_account.Credentials.from_service_account_info(
                        json.loads(creds_json),
                        scopes=["https://www.googleapis.com/auth/gmail.send"]
                    )
                    self._service = build("gmail", "v1", credentials=credentials)
                    logger.info("Gmail service authenticated via environment variable")
                    return self._service
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse GMAIL_CREDENTIALS_FILE JSON: {je}")
                except Exception as e:
                    logger.error(f"Failed to load credentials from env: {e}")

            # Try service account file (for local development)
            # Use absolute path from backend directory
            backend_dir = Path(__file__).parent.parent.parent
            creds_file = backend_dir / "credentials.json"
            
            if creds_file.exists():
                logger.info(f"Found credentials file: {creds_file}")
                credentials = service_account.Credentials.from_service_account_file(
                    str(creds_file),
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
                self._service = build("gmail", "v1", credentials=credentials)
                logger.info(f"Gmail service authenticated via service account file: {creds_file}")
                return self._service

            # Try relative path (fallback)
            creds_file = Path(settings.gmail_credentials_path)
            if creds_file.exists():
                credentials = service_account.Credentials.from_service_account_file(
                    str(creds_file),
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
                self._service = build("gmail", "v1", credentials=credentials)
                logger.info(f"Gmail service authenticated via service account file: {creds_file}")
                return self._service

            # Try absolute path for Render (if file uploaded)
            render_creds_path = Path("/opt/render/project/src/credentials.json")
            if render_creds_path.exists():
                credentials = service_account.Credentials.from_service_account_file(
                    str(render_creds_path),
                    scopes=["https://www.googleapis.com/auth/gmail.send"]
                )
                self._service = build("gmail", "v1", credentials=credentials)
                logger.info(f"Gmail service authenticated via Render file path: {render_creds_path}")
                return self._service

            # Fallback
            logger.warning("No Gmail credentials found. Using SMTP fallback.")
            return None

        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return None

    async def process_notification(self, pubsub_message: dict) -> None:
        """
        Process Gmail Pub/Sub notification.

        Args:
            pubsub_message: Pub/Sub push message with historyId
        """
        try:
            history_id = pubsub_message.get("message", {}).get("attributes", {}).get("historyId")
            if not history_id:
                logger.warning("No historyId in Pub/Sub message")
                return

            # Fetch new messages from Gmail API
            service = self._get_gmail_service()
            if not service:
                logger.warning("Gmail service not available, skipping email fetch")
                return

            # Get history changes
            history = service.users().history().list(
                userId="me",
                startHistoryId=history_id,
                historyTypes=["messageAdded"]
            ).execute()

            if "history" not in history:
                logger.info("No new messages in history")
                return

            for hist_record in history["history"]:
                if "messagesAdded" in hist_record:
                    for msg_added in hist_record["messagesAdded"]:
                        message_id = msg_added["message"]["id"]
                        await self._process_new_email(message_id)

            logger.info(f"Processed Gmail notification: historyId={history_id}")

        except Exception as e:
            logger.error(f"Gmail notification processing failed: {e}")
            raise

    async def _process_new_email(self, message_id: str) -> None:
        """Process a new incoming email."""
        try:
            email_data = await self.get_message(message_id)
            if not email_data:
                return

            # Extract sender email
            from_email = email_data.get("from", "")
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")

            # Parse email address from "Name <email@example.com>" format
            import re
            email_match = re.search(r"<([^>]+)>", from_email)
            if email_match:
                from_email = email_match.group(1)

            # Create or get customer
            pool = await get_pool()
            customer_id = await self._create_or_get_customer(pool, from_email)

            # Create ticket
            ticket_id = await self._create_ticket(pool, customer_id, subject)

            # Store incoming message
            await self._store_message(pool, ticket_id, body)

            # Publish to Kafka for agent processing
            await self._producer.publish(
                TOPICS["email_inbound"],
                {
                    "ticket_id": ticket_id,
                    "customer_id": customer_id,
                    "from": from_email,
                    "subject": subject,
                    "message": body,
                    "thread_id": email_data.get("thread_id", ""),
                    "message_id": message_id,
                }
            )

            logger.info(f"Processed email from {from_email}: {subject[:50]}...")

        except Exception as e:
            logger.error(f"Failed to process new email: {e}")

    async def _create_or_get_customer(self, pool, email: str) -> str:
        """Create or get customer by email."""
        async with pool.acquire() as conn:
            # Check if customer exists
            existing = await conn.fetchrow(
                "SELECT id FROM customers WHERE email = $1", email
            )
            if existing:
                return str(existing["id"])

            # Create new customer
            customer_id = await conn.fetchval(
                "INSERT INTO customers (email) VALUES ($1) RETURNING id", email
            )
            return str(customer_id)

    async def _create_ticket(self, pool, customer_id: str, subject: str) -> str:
        """Create a new ticket."""
        async with pool.acquire() as conn:
            ticket_id = await conn.fetchval(
                """
                INSERT INTO tickets (customer_id, source_channel, subject, priority)
                VALUES ($1, 'email', $2, 'normal')
                RETURNING id
                """,
                customer_id, subject
            )
            return str(ticket_id)

    async def _store_message(self, pool, ticket_id: str, content: str) -> None:
        """Store incoming message in database."""
        async with pool.acquire() as conn:
            # Get conversation_id from ticket
            ticket = await conn.fetchrow(
                "SELECT conversation_id FROM tickets WHERE id = $1", ticket_id
            )
            if ticket:
                await conn.execute(
                    """
                    INSERT INTO messages (conversation_id, channel, direction, role, content)
                    VALUES ($1, 'email', 'incoming', 'customer', $2)
                    """,
                    str(ticket["conversation_id"]), content
                )

    async def get_message(self, message_id: str) -> Optional[Dict[str, str]]:
        """
        Fetch email message from Gmail API.

        Args:
            message_id: Gmail message ID

        Returns:
            Parsed email data or None
        """
        try:
            service = self._get_gmail_service()
            if not service:
                logger.warning("Gmail service not available for fetching message")
                return None

            # Get message from Gmail API
            message = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            # Parse headers
            headers = message.get("payload", {}).get("headers", [])
            email_data = {
                "from": self._get_header(headers, "From"),
                "to": self._get_header(headers, "To"),
                "subject": self._get_header(headers, "Subject"),
                "thread_id": self._get_header(headers, "Thread-Id"),
                "message_id": self._get_header(headers, "Message-ID"),
                "in_reply_to": self._get_header(headers, "In-Reply-To"),
            }

            # Extract body
            email_data["body"] = self._extract_body_from_payload(message.get("payload", {}))

            return email_data

        except Exception as e:
            logger.error(f"Failed to fetch Gmail message {message_id}: {e}")
            return None

    def _get_header(self, headers: List[Dict], name: str) -> str:
        """Extract header value from Gmail headers list."""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header.get("value", "")
        return ""

    def _extract_body_from_payload(self, payload: Dict) -> str:
        """Extract text body from Gmail payload."""
        try:
            # Try multipart first
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8")
                    elif part.get("mimeType") == "text/html":
                        # Prefer plain text, but use HTML if no plain text
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8")

            # Try single part
            if "body" in payload:
                data = payload["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8")

            return ""
        except Exception as e:
            logger.error(f"Failed to extract email body: {e}")
            return ""

    async def send_reply(self, thread_id: str, content: str, in_reply_to: str, to_email: str) -> bool:
        """
        Send email reply via Gmail API or SMTP fallback.

        Args:
            thread_id: Gmail thread ID
            content: Email content
            in_reply_to: Message-ID to reply to
            to_email: Recipient email address

        Returns:
            True if sent successfully
        """
        # For personal Gmail accounts, use SMTP directly (more reliable)
        # Gmail API with service account requires domain-wide delegation (Workspace only)
        try:
            logger.info(f"Using SMTP to send email to {to_email}")
            from src.channels.email_sender import get_email_sender
            email_sender = get_email_sender()
            
            # Extract subject from content or use default
            subject_line = f"Re: Support Request - Ticket #{thread_id[:8]}" if thread_id else "Re: Your Support Request"
            
            success = await email_sender.send_ticket_response(
                to_email=to_email,
                ticket_id=thread_id,
                subject=subject_line,
                response=content,
            )
            
            if success:
                logger.info(f"✅ Email sent successfully via SMTP to {to_email}")
            else:
                logger.warning(f"⚠️ SMTP send returned False")
            
            return success
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}", exc_info=True)
            return False

    def _create_html_reply(self, content: str) -> str:
        """Create HTML version of email reply."""
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
        .content {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="content">
        {content.replace(chr(10), '<br>')}
    </div>
    <div class="footer">
        <p>Best regards,<br><strong>AI Support Team</strong></p>
    </div>
</body>
</html>
"""

    def parse_email(self, raw_message: str) -> dict:
        """
        Parse raw RFC2822 email message.

        Args:
            raw_message: Base64-encoded RFC2822 message

        Returns:
            Parsed email data
        """
        try:
            decoded = base64.urlsafe_b64decode(raw_message)
            msg = BytesParser(policy=default).parsebytes(decoded)

            return {
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "thread_id": msg.get("Message-ID", ""),
                "in_reply_to": msg.get("In-Reply-To", ""),
                "body": self._extract_body(msg),
            }
        except Exception as e:
            logger.error(f"Email parsing failed: {e}")
            return {}

    def _extract_body(self, msg) -> str:
        """Extract text body from email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get_content_disposition())
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        return part.get_payload(decode=True).decode()
                    except Exception:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode()
            except Exception:
                pass
        return ""


# Convenience function for creating handler
def create_gmail_handler(producer: FTEKafkaProducer) -> GmailHandler:
    """Create Gmail handler instance."""
    return GmailHandler(producer)
