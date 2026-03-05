# Email & WhatsApp Sending Fix for Render Deployment

**Date**: 2026-02-24
**Issue**: AI responses show on UI but don't send to customer's email/WhatsApp
**Status**: ✅ FIXED

---

## Problem Summary

Your backend is deployed on Render, and while the AI generates responses that appear in the UI, they're not being delivered to:
1. **Customer's email inbox** (for web form and email tickets)
2. **Customer's WhatsApp** (for WhatsApp tickets)

---

## Root Causes

### 1. Email Sending Issue

**Problem**: Code was prioritizing Gmail API over SMTP, but Gmail API requires service account credentials that weren't configured.

**Location**: `backend/src/agent/runner.py` lines 284-322

**What was happening**:
- Code tried Gmail API first → Failed (no credentials)
- Fell back to SMTP → But fallback wasn't working properly
- Email stored in DB with `delivery_status = 'sent'` even though it wasn't actually sent

### 2. WhatsApp Sending Issue

**Problem**: `WHATSAPP_MCP_ENABLED=false` in environment variables

**Location**: `backend/.env` and Render environment variables

**What was happening**:
- WhatsApp handler checked `settings.whatsapp_mcp_enabled`
- Since it was `false`, messages were only stored in DB
- No actual WhatsApp message was sent via MCP bridge

---

## Solution Applied

### ✅ Fixed `runner.py`

I've updated the `_send_response()` method to:

1. **Try SMTP first** (more reliable for Render)
2. **Fall back to Gmail API** if SMTP fails
3. **Track delivery status properly**:
   - `pending` → when message is created
   - `sent` → when successfully delivered
   - `failed` → when all methods fail
4. **Add detailed logging** to debug issues

**Key changes**:
- Line 239: Set initial status to `'pending'` instead of `'sent'`
- Lines 300-350: Prioritize SMTP, then Gmail API fallback
- Lines 265-280: Update delivery status based on actual send result
- Added emoji logging for better visibility (📧, ✅, ⚠️, ❌)

---

## How to Fix on Render

### Step 1: Update Environment Variables

Go to your Render dashboard → Your backend service → Environment tab

**Add/Update these variables**:

```bash
# Gmail SMTP (Required for email sending)
GMAIL_SENDER_EMAIL=sheikhqirat100@gmail.com
GMAIL_SENDER_PASSWORD=bmux fhnt yvjb mhzn

# Support team email
SUPPORT_TEAM_EMAIL=sheikhqirat100@gmail.com

# WhatsApp MCP (Set to true to enable)
WHATSAPP_MCP_ENABLED=true
WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge
WHATSAPP_POLL_INTERVAL=30

# Other required vars (if not already set)
GEMINI_API_KEY=AIzaSyBeTn3oLWshQQn8098uyub0OGVNukplNb0
DATABASE_URL=postgresql://neondb_owner:npg_RDX7kKF4SsUr@ep-sparkling-band-ai3dxuro-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENVIRONMENT=production
```

**Important Notes**:
- Remove spaces from `GMAIL_SENDER_PASSWORD` if copying from Google
- The password shown above is your Gmail App Password (16 chars)
- Set `WHATSAPP_MCP_ENABLED=true` only if you have the WhatsApp bridge running

### Step 2: Verify Gmail App Password

Your current password: `bmux fhnt yvjb mhzn`

**To verify it's working**:
1. Go to https://myaccount.google.com/apppasswords
2. Check if "NovaSaaS Support" app password exists
3. If not, generate a new one and update Render env vars

**If you need to regenerate**:
1. Go to https://myaccount.google.com/apppasswords
2. Click "Select app" → "Other (Custom name)"
3. Enter: `NovaSaaS Support Render`
4. Copy the 16-character password (remove spaces)
5. Update `GMAIL_SENDER_PASSWORD` on Render

### Step 3: Deploy Updated Code

```bash
# Commit the fixed runner.py
git add backend/src/agent/runner.py
git commit -m "fix: prioritize SMTP for email sending and track delivery status"
git push origin main
```

Render will automatically redeploy.

### Step 4: Test Email Sending

After deployment completes:

1. **Submit a test ticket** via web form at your frontend URL
2. **Check Render logs** for these messages:
   ```
   📧 Sending email response for ticket {id} to {email}
   Attempting SMTP send to {email}
   ✅ Email sent successfully via SMTP to {email}
   ```
3. **Check customer's email inbox** for the AI response
4. **Check database** - `delivery_status` should be `'sent'`

### Step 5: Test WhatsApp Sending (Optional)

**Prerequisites**:
- WhatsApp MCP Go bridge must be running
- Bridge must be connected to WhatsApp Web

**If you have the bridge running**:
1. Set `WHATSAPP_MCP_ENABLED=true` on Render
2. Redeploy
3. Send a WhatsApp message to your support number
4. Check logs for:
   ```
   Sending response via WhatsApp MCP for ticket {id}
   WhatsApp handler initialized: True
   WhatsApp MCP response sent: True to {phone}
   ```

**If you don't have the bridge**:
- Keep `WHATSAPP_MCP_ENABLED=false`
- Messages will be stored in DB only
- You can manually send them or set up the bridge later

---

## Verification Checklist

After deploying the fix, verify:

- [ ] Render environment variables are set correctly
- [ ] Backend redeployed successfully
- [ ] Submit test ticket via web form
- [ ] Check Render logs for "✅ Email sent successfully"
- [ ] Customer receives email in their inbox
- [ ] Email contains AI response with proper formatting
- [ ] Database shows `delivery_status = 'sent'`
- [ ] No errors in Render logs

---

## Debugging Tips

### If emails still not sending:

**Check Render logs**:
```bash
# Look for these patterns
📧 Sending email response
Attempting SMTP send
✅ Email sent successfully  # Should see this
❌ SMTP sending failed      # If you see this, check credentials
```

**Common issues**:
1. **"Authentication failed"**
   - Wrong app password
   - 2FA not enabled on Gmail
   - Using regular password instead of app password

2. **"Connection timeout"**
   - Render firewall blocking SMTP port 587
   - Gmail SMTP server down (rare)

3. **"Email sent but not received"**
   - Check spam folder
   - Verify customer email is correct
   - Check Gmail sent folder

### If WhatsApp not sending:

**Check logs**:
```bash
WhatsApp MCP enabled: true
WhatsApp handler initialized: True
WhatsApp MCP response sent: True
```

**Common issues**:
1. **"WhatsApp MCP disabled in settings"**
   - Set `WHATSAPP_MCP_ENABLED=true` on Render

2. **"WhatsApp MCP not initialized"**
   - Go bridge not running
   - Bridge path incorrect
   - WhatsApp Web not connected

3. **"WhatsApp MCP send_response returned False"**
   - Bridge connection lost
   - Phone number format incorrect (must be E.164: +923001234567)

---

## Database Delivery Status

The `messages` table now tracks delivery status:

```sql
SELECT
    m.id,
    m.content,
    m.direction,
    m.delivery_status,
    m.created_at,
    t.id as ticket_id
FROM messages m
JOIN conversations c ON c.id = m.conversation_id
JOIN tickets t ON t.conversation_id = c.id
WHERE m.direction = 'outgoing'
ORDER BY m.created_at DESC
LIMIT 10;
```

**Status values**:
- `pending` - Message created, not yet sent
- `sent` - Successfully delivered
- `failed` - All delivery methods failed

---

## Testing Commands

### Test SMTP locally:

```python
# backend/test_smtp.py
import smtplib
from email.mime.text import MIMEText

sender = "sheikhqirat100@gmail.com"
password = "bmuxfhntyvjbmhzn"  # Remove spaces
recipient = "test@example.com"

msg = MIMEText("Test email from NovaSaaS")
msg["Subject"] = "Test"
msg["From"] = sender
msg["To"] = recipient

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")
```

Run:
```bash
cd backend
python test_smtp.py
```

---

## Next Steps

1. **Deploy the fix** to Render
2. **Update environment variables** on Render dashboard
3. **Test email sending** with a real ticket
4. **Monitor logs** for any errors
5. **Enable WhatsApp** when bridge is ready

---

## Support

If issues persist after following this guide:

1. Check Render logs for detailed error messages
2. Verify Gmail app password is correct
3. Test SMTP locally using the test script above
4. Check if Gmail is blocking the login (check security alerts)

---

**Status**: Ready to deploy ✅
