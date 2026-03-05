"""IMAP Email Polling - Receive emails without Gmail API domain delegation.

This module polls Gmail via IMAP to receive support emails without requiring
Google Workspace domain-wide delegation.

Requirements:
    - Gmail account with IMAP enabled
    - App password (not regular password)
    - Python imaplib and email modules (standard library)

Setup:
    1. Enable IMAP in Gmail: https://myaccount.google.com/lesssecureapps
    2. Generate App Password: https://myaccount.google.com/apppasswords
    3. Add to .env:
       IMAP_EMAIL=your-email@gmail.com
       IMAP_PASSWORD=your-app-password
       IMAP_POLL_INTERVAL=60
"""

import imaplib
import email
from email.header import decode_header
from typing import Optional, List, Dict, Any
import logging
import asyncio
from datetime import datetime, timedelta
import base64
from pathlib import Path
import pickle

from src.database.connection import get_pool
from src.database import queries
from src.kafka.client import FTEKafkaProducer
from src.kafka.topics import TOPICS
from src.config import get_settings
from src.agent.runner import AgentRunner

logger = logging.getLogger(__name__)
settings = get_settings()


class IMAPEmailPoller:
    """Poll Gmail inbox via IMAP for new support emails."""

    def __init__(
        self,
        imap_server: str = "imap.gmail.com",
        imap_port: int = 993,
    ) -> None:
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.email_address = settings.gmail_sender_email
        self.app_password = settings.gmail_sender_password
        self.poll_interval = getattr(settings, 'imap_poll_interval', 60)
        self._last_uid: Optional[str] = None
        self._state_file = Path("imap_state.pkl")

    def _load_state(self) -> None:
        """Load last processed UID from disk."""
        if self._state_file.exists():
            try:
                with open(self._state_file, "rb") as f:
                    state = pickle.load(f)
                    self._last_uid = state.get("last_uid")
                    logger.info(f"Loaded last processed UID: {self._last_uid}")
            except Exception as e:
                logger.warning(f"Failed to load state file: {e}")

    def _save_state(self) -> None:
        """Save last processed UID to disk."""
        try:
            with open(self._state_file, "wb") as f:
                pickle.dump({"last_uid": self._last_uid}, f)
        except Exception as e:
            logger.warning(f"Failed to save state file: {e}")

    def _connect(self) -> imaplib.IMAP4_SSL:
        """Connect and login to Gmail IMAP server."""
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # Login with app password
            mail.login(self.email_address, self.app_password)
            
            # Select inbox (readonly=False means we can mark as read)
            mail.select("inbox")
            
            logger.info(f"Connected to Gmail IMAP: {self.email_address}")
            return mail
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection failed: {e}")
            raise

    def _decode_mime_words(self, text: str) -> str:
        """Decode MIME encoded words in email headers."""
        if not text:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(text):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8'))
                except (UnicodeDecodeError, LookupError):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        
        return "".join(decoded_parts)

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extract plain text body from email message."""
        body = ""
        
        # If message is multipart
        if msg.is_multipart():
            # Try to get plain text part first
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition") or "")
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(charset, errors='replace')
                            break
                    except Exception as e:
                        logger.warning(f"Failed to decode text part: {e}")
            
            # If no plain text, try HTML
            if not body:
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            payload = part.get_payload(decode=True)
                            if payload:
                                # Simple HTML to text conversion
                                import re
                                html = payload.decode(charset, errors='replace')
                                body = re.sub(r'<[^>]+>', '', html)
                                break
                        except Exception as e:
                            logger.warning(f"Failed to decode HTML part: {e}")
        else:
            # Message is not multipart
            try:
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors='replace')
            except Exception as e:
                logger.warning(f"Failed to decode message body: {e}")
        
        return body.strip()

    async def _process_email(
        self,
        message_id: str,
        from_address: str,
        subject: str,
        body: str,
        received_at: datetime,
    ) -> None:
        """Process a single email: create ticket, run AI, send reply."""
        try:
            pool = await get_pool()
            
            # Extract email address from from_address
            import re
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_address)
            customer_email = email_match.group(0) if email_match else from_address
            
            # Extract name from from_address
            name_match = re.match(r'([^<]+)', from_address)
            customer_name = name_match.group(0).strip() if name_match else "Customer"
            
            # Create or get customer
            customer_id = await queries.create_customer(
                pool, email=customer_email, name=customer_name
            )
            
            # Create ticket
            ticket_id = await queries.create_ticket(
                pool,
                customer_id=customer_id,
                source_channel="email",
                subject=subject or "(No Subject)",
                category="general",
                priority="medium",
            )
            
            # Store incoming message
            ticket_data = await queries.get_ticket_by_id(pool, ticket_id)
            if ticket_data:
                await queries.create_message(
                    pool,
                    conversation_id=ticket_data["conversation_id"],
                    channel="email",
                    direction="incoming",
                    role="customer",
                    content=body,
                )
            
            logger.info(f"Created ticket {ticket_id} from email: {subject}")
            
            # Publish to Kafka for async processing
            producer = FTEKafkaProducer()
            await producer.start()
            await producer.publish(
                TOPICS["email_inbound"],
                {
                    "ticket_id": ticket_id,
                    "customer_id": customer_id,
                    "subject": subject,
                    "message": body,
                    "from_email": customer_email,
                }
            )
            await producer.stop()
            
            # Optionally process immediately with AI
            # runner = AgentRunner()
            # response = await runner.process_ticket(ticket_id)
            # await self._send_reply(customer_email, subject, response)
            
        except Exception as e:
            logger.error(f"Failed to process email: {e}", exc_info=True)

    async def _send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        in_reply_to: Optional[str] = None,
    ) -> None:
        """Send email reply via SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Re: {subject}"
            msg["From"] = self.email_address
            msg["To"] = to_email
            
            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
                msg["References"] = in_reply_to
            
            # Attach plain text and HTML versions
            text_part = MIMEText(body, "plain", "utf-8")
            html_part = MIMEText(
                f"""<html>
                <body>
                    <p>{body.replace(chr(10), '<br>')}</p>
                    <br>
                    <p>Best regards,<br>NovaSaaS AI Support Team</p>
                </body>
                </html>""",
                "html",
                "utf-8"
            )
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send via Gmail SMTP
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)
            
            logger.info(f"Sent email reply to: {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email reply: {e}")

    async def poll_once(self) -> int:
        """Poll inbox once and process new emails.
        
        Returns:
            Number of new emails processed
        """
        mail = None
        processed_count = 0
        
        try:
            # Connect to IMAP
            mail = self._connect()
            
            # Load previous state
            self._load_state()
            
            # Search for emails
            if self._last_uid:
                # Get only new emails since last UID
                _, message_data = mail.uid("search", None, f"UID {self._last_uid}:*")
            else:
                # Get all unread emails on first run
                _, message_data = mail.uid("search", None, "UNSEEN")
            
            # Get list of message UIDs
            uids = message_data[0].split()
            
            if not uids:
                logger.info("No new emails found")
                return 0
            
            logger.info(f"Found {len(uids)} new email(s)")
            
            # Process each email
            for uid in uids:
                try:
                    uid_str = uid.decode("utf-8")
                    
                    # Fetch email by UID
                    _, msg_data = mail.uid("fetch", uid, "(RFC822)")
                    
                    if not msg_data or not msg_data[0]:
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract headers
                    from_address = self._decode_mime_words(msg.get("From", ""))
                    subject = self._decode_mime_words(msg.get("Subject", ""))
                    date_str = msg.get("Date", "")
                    message_id = msg.get("Message-ID", uid_str)
                    
                    # Parse date
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(date_str)
                    except Exception:
                        received_at = datetime.now()
                    
                    # Get body
                    body = self._get_email_body(msg)
                    
                    if not body:
                        logger.warning(f"Empty email body from {from_address}")
                        continue
                    
                    # Process email
                    await self._process_email(
                        message_id=message_id,
                        from_address=from_address,
                        subject=subject,
                        body=body,
                        received_at=received_at,
                    )
                    
                    # Mark as read
                    mail.uid("STORE", uid, "+FLAGS", "\\Seen")
                    
                    # Update last UID
                    self._last_uid = uid_str
                    processed_count += 1
                    
                    logger.info(f"Processed email: {subject} from {from_address}")
                    
                except Exception as e:
                    logger.error(f"Failed to process email UID {uid}: {e}")
                    continue
            
            # Save state
            self._save_state()
            
            logger.info(f"Processed {processed_count} email(s)")
            return processed_count
            
        except Exception as e:
            logger.error(f"IMAP polling failed: {e}", exc_info=True)
            return 0
            
        finally:
            # Close connection
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass

    async def poll_continuously(self) -> None:
        """Poll inbox continuously at configured interval."""
        logger.info(f"Starting continuous IMAP polling (interval: {self.poll_interval}s)")
        
        while True:
            try:
                await self.poll_once()
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            await asyncio.sleep(self.poll_interval)


async def main():
    """Run IMAP poller."""
    import argparse
    
    parser = argparse.ArgumentParser(description="IMAP Email Poller")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Poll once and exit"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Poll interval in seconds"
    )
    
    args = parser.parse_args()
    
    poller = IMAPEmailPoller()
    
    if args.interval:
        poller.poll_interval = args.interval
    
    if args.once:
        count = await poller.poll_once()
        print(f"Processed {count} email(s)")
    else:
        await poller.poll_continuously()


if __name__ == "__main__":
    asyncio.run(main())
