"""Test Gmail API integration."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.channels.gmail_handler import GmailHandler
from src.kafka.client import FTEKafkaProducer
from src.config import get_settings

settings = get_settings()


async def test_gmail_service():
    """Test Gmail API authentication and service."""
    print("=" * 60)
    print("Testing Gmail API Integration")
    print("=" * 60)
    
    # Create handler
    producer = FTEKafkaProducer()
    await producer.start()
    
    handler = GmailHandler(producer)
    
    # Test 1: Get Gmail service
    print("\n[1/3] Testing Gmail API authentication...")
    service = handler._get_gmail_service()
    
    if service:
        print("✓ Gmail service authenticated successfully")
        
        # Test 2: Get profile
        print("\n[2/3] Fetching Gmail profile...")
        try:
            profile = service.users().getProfile(userId="me").execute()
            print(f"✓ Connected to: {profile.get('emailAddress', 'Unknown')}")
            print(f"  Messages in inbox: {profile.get('messagesTotal', 'Unknown')}")
            print(f"  Threads in inbox: {profile.get('threadsTotal', 'Unknown')}")
        except Exception as e:
            print(f"✗ Failed to fetch profile: {e}")
            print("  Note: Service account may not have access to Gmail")
            print("  You need to delegate domain-wide authority to the service account")
        
        # Test 3: List recent messages
        print("\n[3/3] Listing recent messages...")
        try:
            messages = service.users().messages().list(
                userId="me",
                maxResults=5
            ).execute()
            
            if messages.get("messages"):
                print(f"✓ Found {len(messages['messages'])} recent messages")
                for msg in messages["messages"][:3]:
                    msg_detail = service.users().messages().get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"]
                    ).execute()
                    
                    headers = msg_detail.get("payload", {}).get("headers", [])
                    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No subject")
                    from_addr = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
                    
                    print(f"  - From: {from_addr}")
                    print(f"    Subject: {subject}")
                    print()
            else:
                print("  No messages found")
                
        except Exception as e:
            print(f"✗ Failed to list messages: {e}")
    
    else:
        print("✗ Gmail service authentication failed")
        print("  Checking credentials...")
        
        creds_path = Path("credentials.json")
        if creds_path.exists():
            print(f"  ✓ credentials.json found")
        else:
            print(f"  ✗ credentials.json not found at {creds_path}")
    
    # Cleanup
    await producer.stop()
    
    print("\n" + "=" * 60)
    print("Gmail API Test Complete")
    print("=" * 60)


async def test_email_sending():
    """Test sending email via Gmail API."""
    print("\n" + "=" * 60)
    print("Testing Email Sending")
    print("=" * 60)
    
    producer = FTEKafkaProducer()
    await producer.start()
    
    handler = GmailHandler(producer)
    
    # Test sending a reply
    print("\nSending test email...")
    print(f"  To: {settings.gmail_sender_email}")
    print("  Subject: Test from Gmail API")
    
    success = await handler.send_reply(
        thread_id="test_thread",
        content="This is a test email sent from the Gmail API integration.",
        in_reply_to="test_message_id",
        to_email=settings.gmail_sender_email,
    )
    
    if success:
        print("✓ Email sent successfully!")
    else:
        print("✗ Email sending failed")
        print("  Falling back to SMTP...")
        
        # Try SMTP fallback
        from src.channels.email_sender import get_email_sender
        sender = get_email_sender()
        smtp_success = await sender.send_ticket_response(
            to_email=settings.gmail_sender_email,
            ticket_id="test_ticket_123",
            subject="Test from SMTP",
            response="This is a test email sent via SMTP fallback.",
        )
        
        if smtp_success:
            print("✓ Email sent successfully via SMTP!")
        else:
            print("✗ SMTP sending also failed")
    
    await producer.stop()
    
    print("\n" + "=" * 60)
    print("Email Sending Test Complete")
    print("=" * 60)


async def main():
    """Run all tests."""
    await test_gmail_service()
    await test_email_sending()
    
    print("\n\nNext Steps:")
    print("1. Check your Gmail inbox for test emails")
    print("2. If Gmail API failed, ensure service account has Gmail API access")
    print("3. For production, enable Gmail Pub/Sub notifications")
    print("4. Test web form submission at http://localhost:3000/support")


if __name__ == "__main__":
    asyncio.run(main())
