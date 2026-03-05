"""
Test email sending with Gmail SMTP.

Run this script to verify your Gmail credentials work before deploying to Render.

Usage:
    python test_email_sending.py
"""
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings

def test_smtp_connection():
    """Test SMTP connection and authentication."""
    print("🔍 Testing Gmail SMTP connection...\n")

    settings = get_settings()

    # Check if credentials are set
    if not settings.gmail_sender_email:
        print("❌ GMAIL_SENDER_EMAIL not set in .env")
        return False

    if not settings.gmail_sender_password:
        print("❌ GMAIL_SENDER_PASSWORD not set in .env")
        return False

    print(f"📧 Sender Email: {settings.gmail_sender_email}")
    print(f"🔑 Password: {'*' * len(settings.gmail_sender_password)} ({len(settings.gmail_sender_password)} chars)")
    print()

    try:
        # Test connection
        print("1️⃣ Connecting to smtp.gmail.com:587...")
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        print("   ✅ Connected")

        # Test TLS
        print("2️⃣ Starting TLS encryption...")
        server.starttls()
        print("   ✅ TLS enabled")

        # Test authentication
        print("3️⃣ Authenticating...")
        server.login(settings.gmail_sender_email, settings.gmail_sender_password)
        print("   ✅ Authentication successful")

        server.quit()
        print("\n✅ All tests passed! SMTP is configured correctly.\n")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you're using an App Password, not your regular Gmail password")
        print("   2. Generate one at: https://myaccount.google.com/apppasswords")
        print("   3. Enable 2-Factor Authentication first")
        print("   4. Remove spaces from the app password")
        return False

    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP error: {e}")
        return False

    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        print("\n💡 Check your internet connection")
        return False


def send_test_email(to_email: str):
    """Send a test email."""
    print(f"\n📨 Sending test email to {to_email}...\n")

    settings = get_settings()

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🤖 Test Email from Customer Success FTE"
        msg["From"] = settings.gmail_sender_email
        msg["To"] = to_email

        # Plain text version
        text = """
Hello!

This is a test email from your Customer Success FTE system.

If you're receiving this, your Gmail SMTP configuration is working correctly! 🎉

You can now deploy to Render with confidence.

Best regards,
Customer Success FTE Bot
"""

        # HTML version
        html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            color: white;
            padding: 24px;
            border-radius: 12px 12px 0 0;
            text-align: center;
        }
        .content {
            background: white;
            padding: 32px;
            border: 1px solid #e5e7eb;
            border-top: none;
        }
        .success {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 16px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }
        .footer {
            background: #f9fafb;
            padding: 24px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
            border: 1px solid #e5e7eb;
            border-top: none;
            border-radius: 0 0 12px 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Customer Success FTE</h1>
        <p style="margin: 0; opacity: 0.9;">Test Email</p>
    </div>

    <div class="content">
        <h2>Hello! 👋</h2>

        <p>This is a test email from your <strong>Customer Success FTE</strong> system.</p>

        <div class="success">
            <strong>✅ Success!</strong><br>
            If you're receiving this, your Gmail SMTP configuration is working correctly!
        </div>

        <p>You can now deploy to Render with confidence. Your AI agent will be able to send email responses to customers.</p>

        <h3>What's Next?</h3>
        <ul>
            <li>Deploy your backend to Render</li>
            <li>Set environment variables on Render dashboard</li>
            <li>Test with a real support ticket</li>
            <li>Monitor logs for delivery confirmation</li>
        </ul>

        <p style="margin-top: 24px;">
            Best regards,<br>
            <strong>Customer Success FTE Bot</strong>
        </p>
    </div>

    <div class="footer">
        <p>This is an automated test email.</p>
        <p style="margin-top: 12px; font-size: 12px;">
            © 2026 Customer Success FTE. Powered by Google Gemini AI.
        </p>
    </div>
</body>
</html>
"""

        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        # Send email
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(settings.gmail_sender_email, settings.gmail_sender_password)
            server.sendmail(settings.gmail_sender_email, to_email, msg.as_string())

        print(f"✅ Test email sent successfully to {to_email}!")
        print(f"\n💡 Check your inbox (and spam folder) for the test email.\n")
        return True

    except Exception as e:
        print(f"❌ Failed to send test email: {e}\n")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("  Customer Success FTE - Email Sending Test")
    print("=" * 60)
    print()

    # Test SMTP connection
    if not test_smtp_connection():
        print("\n⚠️  Fix the SMTP configuration before proceeding.\n")
        return

    # Ask if user wants to send test email
    print("=" * 60)
    response = input("\n📬 Do you want to send a test email? (y/n): ").strip().lower()

    if response == 'y':
        to_email = input("📧 Enter recipient email address: ").strip()
        if to_email:
            send_test_email(to_email)
        else:
            print("❌ No email address provided")
    else:
        print("\n✅ SMTP test completed. You're ready to deploy!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
