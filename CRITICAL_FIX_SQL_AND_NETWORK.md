# Critical Fix - SQL Syntax Error & Network Issue

**Date**: 2026-02-24 15:00 UTC
**Status**: ✅ SQL Fixed - Network Issue Identified

---

## 🔴 Issues Found

### Issue 1: SQL Syntax Error (FIXED)
```
ERROR: syntax error at or near "ORDER"
```

**Cause**: PostgreSQL doesn't allow `ORDER BY` in `UPDATE` statements without a subquery.

**Fixed**: All 5 instances in `runner.py` now use subquery syntax.

### Issue 2: Network Unreachable (NEEDS ATTENTION)
```
ERROR: Failed to send email: [Errno 101] Network is unreachable
```

**Cause**: Render's network cannot reach Gmail SMTP server (smtp.gmail.com:587)

**Possible reasons**:
1. Render free tier blocks outbound SMTP connections
2. Firewall blocking port 587
3. Network configuration issue

---

## ✅ SQL Fix Applied

### Before (Broken)
```python
UPDATE messages SET delivery_status = 'sent'
WHERE conversation_id = $1 AND direction = 'outgoing'
ORDER BY created_at DESC LIMIT 1  # ❌ Syntax error!
```

### After (Fixed)
```python
UPDATE messages SET delivery_status = 'sent'
WHERE id = (
    SELECT id FROM messages
    WHERE conversation_id = $1 AND direction = 'outgoing'
    ORDER BY created_at DESC LIMIT 1
)  # ✅ Correct syntax!
```

---

## 🔧 Network Issue Solutions

### Solution 1: Use Gmail API Instead of SMTP (RECOMMENDED)

Since Render blocks SMTP, use Gmail API which works over HTTPS (port 443).

**Steps**:

1. **Create Google Cloud Project**
   - Go to: https://console.cloud.google.com/
   - Create new project: "Customer Success FTE"

2. **Enable Gmail API**
   - Go to: APIs & Services → Library
   - Search "Gmail API"
   - Click "Enable"

3. **Create Service Account**
   - Go to: APIs & Services → Credentials
   - Click "Create Credentials" → "Service Account"
   - Name: `customer-success-fte-sender`
   - Click "Create and Continue"
   - Skip optional steps, click "Done"

4. **Create Service Account Key**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON"
   - Download the JSON file

5. **Enable Domain-Wide Delegation (if using Google Workspace)**
   - In service account details, click "Show Domain-Wide Delegation"
   - Enable "Enable Google Workspace Domain-wide Delegation"
   - Note the Client ID

6. **Add to Render Environment Variables**

   Open the downloaded JSON file and copy its entire content.

   Go to Render Dashboard → Backend Service → Environment

   Add this variable:
   ```bash
   GMAIL_CREDENTIALS_FILE={"type":"service_account","project_id":"your-project",...}
   ```

   Paste the entire JSON content as the value (on one line).

7. **Redeploy**

   Render will automatically redeploy. The code will now use Gmail API instead of SMTP.

---

### Solution 2: Use SendGrid (Alternative)

If Gmail API is too complex, use SendGrid (free tier: 100 emails/day).

**Steps**:

1. **Sign up for SendGrid**
   - Go to: https://sendgrid.com/
   - Create free account

2. **Create API Key**
   - Go to: Settings → API Keys
   - Click "Create API Key"
   - Name: `customer-success-fte`
   - Permissions: "Full Access"
   - Copy the API key

3. **Update Code**

   Install SendGrid:
   ```bash
   cd backend
   uv add sendgrid
   ```

   Update `email_sender.py` to use SendGrid instead of SMTP.

4. **Add to Render**
   ```bash
   SENDGRID_API_KEY=your_api_key_here
   SENDGRID_FROM_EMAIL=sheikhqirat100@gmail.com
   ```

---

### Solution 3: Use Render's SMTP Relay (If Available)

Check if Render provides an SMTP relay service for paid plans.

---

## 🚀 Quick Deploy (SQL Fix)

```bash
# Commit the SQL fix
git add backend/src/agent/runner.py
git commit -m "fix: SQL syntax error in UPDATE statements with ORDER BY"
git push origin main
```

This will fix the SQL error, but emails still won't send due to network issue.

---

## 📋 Recommended Action Plan

### Immediate (5 minutes)
1. ✅ Deploy SQL fix (done above)
2. ✅ Verify no more SQL errors in logs

### Short-term (30 minutes)
1. Set up Gmail API (Solution 1 above)
2. Add `GMAIL_CREDENTIALS_FILE` to Render
3. Redeploy and test

### Alternative (15 minutes)
1. Set up SendGrid (Solution 2 above)
2. Update code to use SendGrid
3. Redeploy and test

---

## 🔍 How to Verify Gmail API Setup

After setting up Gmail API, test locally:

```python
# backend/test_gmail_api.py
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials from env
creds_json = os.getenv("GMAIL_CREDENTIALS_FILE")
credentials = service_account.Credentials.from_service_account_info(
    json.loads(creds_json),
    scopes=["https://www.googleapis.com/auth/gmail.send"]
)

# Build service
service = build("gmail", "v1", credentials=credentials)

print("✅ Gmail API authenticated successfully!")
```

Run:
```bash
export GMAIL_CREDENTIALS_FILE='{"type":"service_account",...}'
python test_gmail_api.py
```

---

## 📊 Current Status

### ✅ Fixed
- SQL syntax errors in all UPDATE statements
- Proper subquery syntax for PostgreSQL

### ⚠️ Still Broken
- Email sending (network unreachable)
- SMTP blocked by Render

### 🔜 Next Steps
1. Choose solution (Gmail API recommended)
2. Set up credentials
3. Add to Render environment
4. Redeploy
5. Test email delivery

---

## 💡 Why SMTP Doesn't Work on Render

Many cloud platforms (including Render free tier) block outbound SMTP connections on port 25, 465, and 587 to prevent spam. This is why you're seeing "Network is unreachable".

**Solutions that work**:
- ✅ Gmail API (HTTPS port 443)
- ✅ SendGrid API (HTTPS port 443)
- ✅ Mailgun API (HTTPS port 443)
- ✅ AWS SES API (HTTPS port 443)
- ❌ Direct SMTP (ports 25, 465, 587 blocked)

---

## 📞 Need Help?

If you need help setting up Gmail API, let me know and I can guide you through each step!

---

**Status**: SQL fixed, ready to deploy. Email sending requires Gmail API setup.
