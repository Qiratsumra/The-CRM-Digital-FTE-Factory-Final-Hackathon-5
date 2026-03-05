"""Test Gmail API and SMTP sending."""
import asyncio
import os
from pathlib import Path

# Test 1: Check credentials file
print("=" * 60)
print("Test 1: Checking credentials.json")
print("=" * 60)
creds_file = Path("credentials.json")
if creds_file.exists():
    print(f"✅ credentials.json found at: {creds_file.absolute()}")
    import json
    with open(creds_file) as f:
        creds = json.load(f)
    print(f"   Type: {creds.get('type', 'unknown')}")
    print(f"   Client Email: {creds.get('client_email', 'unknown')}")
    print(f"   Project ID: {creds.get('project_id', 'unknown')}")
else:
    print(f"❌ credentials.json NOT found")

# Test 2: Try Gmail API
print("\n" + "=" * 60)
print("Test 2: Testing Gmail API")
print("=" * 60)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    
    credentials = service_account.Credentials.from_service_account_file(
        str(creds_file),
        scopes=SCOPES
    )
    
    service = build("gmail", "v1", credentials=credentials)
    print(f"✅ Gmail API service created successfully")
    print(f"   Service account: {credentials.service_account_email}")
    
    # Try to send a test email (will fail without domain delegation)
    print("\n   Attempting to send test email...")
    # Note: This will likely fail for personal Gmail accounts
    # Service accounts need domain-wide delegation
    
except Exception as e:
    print(f"❌ Gmail API test failed: {e}")
    print(f"   This is expected for personal Gmail accounts")
    print(f"   Service accounts need domain-wide delegation")

# Test 3: Try SMTP
print("\n" + "=" * 60)
print("Test 3: Testing SMTP (Gmail App Password)")
print("=" * 60)

import smtplib
from email.mime.text import MIMEText
from src.config import get_settings

settings = get_settings()
print(f"   Sender Email: {settings.gmail_sender_email}")
print(f"   Password set: {'✅' if settings.gmail_sender_password else '❌'}")

if settings.gmail_sender_email and settings.gmail_sender_password:
    try:
        msg = MIMEText("This is a test email from the Customer Success FTE system.")
        msg["Subject"] = "SMTP Test - Customer Success FTE"
        msg["From"] = settings.gmail_sender_email
        msg["To"] = settings.gmail_sender_email  # Send to self for testing
        
        print(f"   Connecting to smtp.gmail.com:587...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.set_debuglevel(1)
            server.starttls()
            print(f"   Logging in as {settings.gmail_sender_email}...")
            server.login(settings.gmail_sender_email, settings.gmail_sender_password)
            print(f"   Sending test email...")
            server.sendmail(settings.gmail_sender_email, settings.gmail_sender_email, msg.as_string())
        
        print(f"✅ SMTP test PASSED - Email sent successfully!")
        print(f"   Check your inbox at {settings.gmail_sender_email}")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print(f"   Possible issues:")
        print(f"   1. App password is incorrect")
        print(f"   2. 2-Step Verification not enabled")
        print(f"   3. App password has spaces (remove them)")
        print(f"   4. Gmail blocked the login attempt")
    except Exception as e:
        print(f"❌ SMTP test failed: {e}")
else:
    print(f"❌ Gmail credentials not configured in .env")
    print(f"   Add these to backend/.env:")
    print(f"   GMAIL_SENDER_EMAIL=your-email@gmail.com")
    print(f"   GMAIL_SENDER_PASSWORD=your-app-password")

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("For personal Gmail accounts, use SMTP (Test 3)")
print("Service accounts (Test 2) require domain-wide delegation")
print("which is only available for Google Workspace accounts.")
print("\nRecommended: Use SMTP with Gmail App Password")
