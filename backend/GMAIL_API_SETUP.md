# Gmail API Integration Setup Guide

## Overview

This guide explains how to set up Gmail API integration for receiving and sending emails in the Customer Success FTE.

## Current Status

✅ **Completed:**
- Gmail API client library installed
- Service account credentials configured (`credentials.json`)
- Gmail handler implemented with send/receive capabilities
- SMTP fallback configured for sending emails

⚠️ **Requires Manual Setup:**
- Enable Gmail API in Google Cloud Console
- Grant service account access to Gmail (domain delegation)

---

## Option 1: Using Service Account (Recommended for Production)

### Step 1: Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `gmail-automation-app-crms`
3. Navigate to **APIs & Services > Library**
4. Search for "Gmail API" and click **Enable**

### Step 2: Grant Domain-Wide Delegation

For the service account to access Gmail, you need to delegate authority:

1. Go to **IAM & Admin > Service Accounts**
2. Click on `crms-371@gmail-automation-app-crms.iam.gserviceaccount.com`
3. Go to the **Domain-wide Delegation** tab
4. Check **Enable G Suite Domain-wide Delegation**
5. Copy the **Client ID**
6. Go to [Google Admin Console](https://admin.google.com/) (requires Google Workspace admin)
7. Navigate to **Security > API Controls > Domain-wide Delegation**
8. Click **Add New**
9. Paste the Client ID
10. Add scopes:
    - `https://www.googleapis.com/auth/gmail.modify`
    - `https://www.googleapis.com/auth/gmail.send`
    - `https://www.googleapis.com/auth/gmail.read`
11. Click **Authorize**

### Step 3: Share Gmail Inbox with Service Account

1. Open your Gmail (sheikhqirat100@gmail.com)
2. Go to **Settings > See all settings > Accounts and Import**
3. Under "Grant access to your account", click **Add another account**
4. Enter the service account email: `crms-371@gmail-automation-app-crms.iam.gserviceaccount.com`
5. Click **Next > Send email to grant access**
6. Accept the delegation request

---

## Option 2: Using OAuth 2.0 (Recommended for Development)

For development without domain delegation, use OAuth 2.0:

### Step 1: Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Credentials**
3. Click **Create Credentials > OAuth client ID**
4. Choose **Desktop app**
5. Download the credentials as `client_secret.json`

### Step 2: Run OAuth Flow

Create a script to authenticate and save tokens:

```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save credentials
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("Authentication successful! Token saved.")
```

### Step 3: Update Gmail Handler

Modify `gmail_handler.py` to use `token.pickle` instead of service account.

---

## Option 3: Using SMTP Only (Quick Start)

For immediate testing without Gmail API setup:

### Current Configuration

Your `.env` already has SMTP credentials:

```env
GMAIL_SENDER_EMAIL=sheikhqirat100@gmail.com
GMAIL_SENDER_PASSWORD="bmux fhnt yvjb mhzn"
```

### How It Works

1. **Sending**: Emails are sent via Gmail SMTP (already working)
2. **Receiving**: Manual webhook testing or use Gmail filters to forward emails

### Testing Email Receiving (Without Gmail API)

1. **Manual Webhook Test**: Use the `/webhooks/gmail` endpoint with test data
2. **Email Forwarding**: Set up Gmail filter to forward support emails to a webhook URL
3. **IMAP Polling**: Implement IMAP polling (can be added if needed)

---

## Testing the Integration

### Test 1: Run Integration Test Script

```bash
cd backend
python test_gmail_integration.py
```

This will:
- Test Gmail API authentication
- Fetch Gmail profile
- List recent messages
- Send a test email

### Test 2: Test Web Form to Email Flow

1. Start the backend:
   ```bash
   uvicorn src.api.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Go to `http://localhost:3000/support`
4. Fill out the form with your email
5. Submit the ticket
6. Check your email for the AI response

### Test 3: Test Gmail Webhook

Send a POST request to `/webhooks/gmail`:

```bash
curl -X POST http://localhost:8000/webhooks/gmail \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "attributes": {
        "historyId": "0"
      }
    }
  }'
```

---

## Troubleshooting

### Error: "insufficientPermission"

**Cause**: Service account doesn't have Gmail API access.

**Solution**: 
- Enable Gmail API in Google Cloud Console
- Grant domain-wide delegation (Option 1)
- Or use OAuth 2.0 (Option 2)

### Error: "credentials invalid"

**Cause**: Wrong credentials or expired token.

**Solution**:
- Verify `credentials.json` is valid
- Check service account email matches
- Regenerate credentials if needed

### Error: "SMTP authentication failed"

**Cause**: Wrong app password or 2FA not enabled.

**Solution**:
1. Enable 2FA on Gmail account
2. Generate new app password: https://myaccount.google.com/apppasswords
3. Update `.env` with new password

### Emails Not Being Received

**Cause**: Gmail Pub/Sub not configured.

**Solution**:
1. Set up Gmail Pub/Sub topic in Google Cloud
2. Create push subscription pointing to your webhook URL
3. Or use IMAP polling as alternative

---

## Production Deployment

For production, you need:

1. **Gmail Pub/Sub Setup**:
   ```bash
   # Create Pub/Sub topic
   gcloud pubsub topics create gmail-push
   
   # Create push subscription
   gcloud pubsub subscriptions create gmail-sub \
     --topic=gmail-push \
     --push-endpoint=https://your-api.com/webhooks/gmail
   ```

2. **Gmail Watch**:
   ```python
   # Set up watch on inbox
   service.users().watch(userId="me", body={
     'topicName': 'projects/your-project/topics/gmail-push'
   }).execute()
   ```

3. **Environment Variables**:
   ```env
   GMAIL_PUBSUB_TOPIC=projects/your-project/topics/gmail-push
   GMAIL_API_ENABLED=true
   ```

---

## Current Implementation Summary

### What's Working Now:

✅ **Sending Emails**:
- Web form submissions trigger AI responses
- Responses sent via Gmail SMTP
- HTML formatted emails with ticket details

✅ **Receiving Emails** (with Gmail API access):
- Gmail webhook processes Pub/Sub notifications
- Creates tickets from incoming emails
- Stores messages in database
- Triggers AI agent for responses

✅ **Fallback**:
- If Gmail API unavailable, falls back to SMTP for sending
- Graceful degradation

### What Needs Gmail API Access:

⏳ **Receiving Emails from Gmail**:
- Requires service account delegation or OAuth
- Without this, use web form for testing

⏳ **Email Threading**:
- Proper In-Reply-To headers
- Thread tracking in Gmail

---

## Next Steps

1. **For Demo**: Use web form + SMTP sending (fully working)
2. **For Production**: Complete Gmail API setup with domain delegation
3. **For Testing**: Run `test_gmail_integration.py` to verify setup

## Support

If you encounter issues:
1. Check logs: `docker compose logs -f api`
2. Verify credentials: Ensure `credentials.json` is valid
3. Test SMTP first: It's easier to set up than full Gmail API
4. Check Gmail API quotas: https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas
