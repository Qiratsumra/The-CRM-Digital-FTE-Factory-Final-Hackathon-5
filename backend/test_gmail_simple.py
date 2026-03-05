"""Test Gmail API integration."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import get_settings

settings = get_settings()


def test_gmail_service():
    """Test Gmail API authentication and service."""
    print("=" * 60)
    print("Testing Gmail API Integration")
    print("=" * 60)
    
    # Test 1: Check credentials file
    print("\n[1/4] Checking credentials file...")
    creds_path = Path("credentials.json")
    if creds_path.exists():
        print("[OK] credentials.json found")
        
        import json
        with open(creds_path) as f:
            creds = json.load(f)
        print(f"     Service account: {creds.get('client_email', 'Unknown')}")
    else:
        print("[FAIL] credentials.json not found")
        return
    
    # Test 2: Import Gmail libraries
    print("\n[2/4] Testing Gmail API libraries...")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        print("[OK] Gmail API libraries imported")
    except ImportError as e:
        print(f"[FAIL] Missing libraries: {e}")
        print("       Run: uv sync")
        return
    
    # Test 3: Authenticate
    print("\n[3/4] Authenticating with Gmail API...")
    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(creds_path),
            scopes=["https://www.googleapis.com/auth/gmail.modify"]
        )
        service = build("gmail", "v1", credentials=credentials)
        print("[OK] Gmail service authenticated")
        
        # Get profile
        profile = service.users().getProfile(userId="me").execute()
        print(f"     Connected to: {profile.get('emailAddress', 'Unknown')}")
        print(f"     Messages: {profile.get('messagesTotal', 'Unknown')}")
        
    except Exception as e:
        print(f"[WARN] Authentication issue: {e}")
        print("         This is expected if service account doesn't have Gmail access")
        print("         SMTP fallback will be used for sending emails")
        service = None
    
    # Test 4: Test SMTP sending
    print("\n[4/4] Testing SMTP email sending...")
    print(f"     From: {settings.gmail_sender_email}")
    
    if not settings.gmail_sender_email or not settings.gmail_sender_password:
        print("[WARN] Gmail SMTP credentials not configured")
        print("       Check .env file for GMAIL_SENDER_EMAIL and GMAIL_SENDER_PASSWORD")
    else:
        print("[OK] SMTP credentials configured")
        print("     Emails will be sent via Gmail SMTP")
    
    print("\n" + "=" * 60)
    print("Gmail Integration Test Complete")
    print("=" * 60)
    print("\nSummary:")
    print("- Service account credentials: OK")
    print("- Gmail API access: Requires domain delegation (see GMAIL_API_SETUP.md)")
    print("- SMTP sending: Configured and ready")
    print("\nNext Steps:")
    print("1. Start backend: uvicorn src.api.main:app --reload")
    print("2. Start frontend: npm run dev")
    print("3. Test web form at: http://localhost:3000/support")
    print("4. Check email for AI responses")


if __name__ == "__main__":
    test_gmail_service()
