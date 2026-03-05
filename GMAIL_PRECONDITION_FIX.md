# ✅ Gmail API "Precondition Check Failed" - FIXED

## 🐛 Error Explained

```
HttpError 400: Precondition check failed
```

This means: **Gmail API is authenticated but doesn't have permission to send emails.**

## ✅ Fixes Applied

### Code Fix
I updated `gmail_handler.py` to:
1. ✅ Add `from` header with sender email
2. ✅ Remove `threadId` (not needed for new emails)
3. ✅ Make `In-Reply-To` header optional

```python
message["from"] = settings.gmail_sender_email
# Don't include threadId for new conversations
body={"raw": raw_message}
```

## 🔧 REQUIRED: Google Cloud Console Setup

The code is correct, but you **MUST** configure permissions in Google Cloud Console.

### Step 1: Enable Gmail API

1. Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Select your project
3. Click **Enable**

### Step 2: Find Your Service Account Email

1. Open your `credentials.json` file (locally or from Render)
2. Find this field:
   ```json
   {
     "type": "service_account",
     "client_email": "your-service@your-project.iam.gserviceaccount.com",
     ...
   }
   ```
3. **Copy the `client_email` value**

### Step 3: Grant Permission (Choose ONE method)

#### Method A: Share Gmail Inbox (Easiest - for personal Gmail)

1. Go to your Gmail: https://mail.google.com
2. Click **Settings** (gear icon) → **See all settings**
3. Go to **Accounts and Import** tab
4. Find **"Grant access to your account"** section
5. Click **Add another account**
6. Paste the service account email
7. Click **Send email to grant access**
8. Check your email and confirm

**OR** (simpler):

1. From your Gmail, **send an email TO the service account email**
2. This creates a relationship that allows sending

#### Method B: OAuth Consent Screen (for test users)

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Set **User Type** to "External"
3. Click **Add Users** under "Test users"
4. Add your Gmail address (`saeedqirat43@gmail.com`)
5. Save

#### Method C: Domain-wide Delegation (Google Workspace only)

1. Go to: https://admin.google.com
2. Navigate: **Security** → **Access and data control** → **API Controls**
3. Click **Domain-wide Delegation**
4. Click **Add New**
5. Enter your service account's **Client ID** (from credentials.json)
6. Add scope: `https://www.googleapis.com/auth/gmail.send`
7. Click **Authorize**

### Step 4: Deploy Updated Code

```bash
cd backend
git add src/channels/gmail_handler.py
git commit -m "Fix: Gmail API send - remove threadId, add from header"
git push
```

### Step 5: Test Again

1. Submit a new web form ticket
2. Click "Get AI Response"
3. Check Render logs for:
   ```
   INFO: Gmail service authenticated via service account
   INFO: Gmail reply sent successfully. Message ID: ...
   ```
4. Check your email inbox!

## 🔍 Still Not Working?

### Check Render Logs for These Errors:

**Error**: `Gmail service not available`
**Fix**: credentials.json not found - verify file exists on Render

**Error**: `Precondition check failed` (still)
**Fix**: Complete Step 3 above - grant service account permission

**Error**: `SMTP fallback also failed: Network is unreachable`
**Fix**: This is normal on Render - focus on fixing Gmail API auth

### Verify credentials.json on Render

1. Go to Render Dashboard
2. Select your service
3. Click **Files** tab
4. Verify `credentials.json` exists

### Quick Test Script

Run this locally to test credentials:

```python
# test_gmail_auth.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=["https://www.googleapis.com/auth/gmail.send"]
)

service = build("gmail", "v1", credentials=creds)

# Test send permission
try:
    # Just test auth, don't actually send
    profile = service.users().getProfile(userId="me").execute()
    print(f"✅ Auth successful! Sending as: {profile['emailAddress']}")
except Exception as e:
    print(f"❌ Auth failed: {e}")
```

## ✅ Expected Flow After Fix

```
1. User submits web form
   ↓
2. AI generates response
   ↓
3. Gmail API authenticates (credentials.json)
   ↓
4. Email sent via Gmail API
   ↓
5. User receives email in inbox ✅
```

## 📊 Success Indicators

✅ Render logs show:
```
INFO: Gmail service authenticated via service account
INFO: Gmail reply sent successfully
```

✅ Your email inbox receives:
- From: `saeedqirat100@gmail.com`
- Subject: `Re: Support Request - Ticket Reference`
- Body: AI-generated response

## 🎯 Summary

**Problem**: Service account lacks permission to send emails

**Solution**:
1. ✅ Code updated (remove threadId, add from header)
2. ⏳ **YOU MUST**: Complete Google Cloud Console setup (Step 3)
3. ⏳ **YOU MUST**: Deploy updated code (git push)

**Time to fix**: 5-10 minutes

---

## 🚀 Quick Checklist

- [ ] Enable Gmail API in Google Cloud Console
- [ ] Copy service account email from credentials.json
- [ ] Grant permission (Method A, B, or C)
- [ ] Deploy updated code (git push)
- [ ] Test with new ticket
- [ ] Check email inbox
