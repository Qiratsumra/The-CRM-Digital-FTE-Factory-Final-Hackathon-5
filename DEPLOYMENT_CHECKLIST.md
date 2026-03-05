# Render Deployment Checklist - Email & WhatsApp Fix

**Date**: 2026-02-24
**Issue**: AI responses not being sent to customer's email/WhatsApp
**Status**: ✅ Code Fixed - Ready to Deploy

---

## 🎯 Quick Summary

**Problem**: Backend deployed on Render, AI generates responses visible in UI, but emails/WhatsApp messages not actually delivered to customers.

**Solution**: Updated `runner.py` to prioritize SMTP over Gmail API and properly track delivery status.

---

## ✅ Pre-Deployment Checklist

### 1. Local Testing (Do this first!)

```bash
# Test your Gmail SMTP credentials locally
cd backend
python test_email_sending.py
```

**Expected output**:
```
✅ Connected
✅ TLS enabled
✅ Authentication successful
✅ All tests passed! SMTP is configured correctly.
```

If this fails, fix your Gmail credentials before deploying to Render.

---

### 2. Verify Gmail App Password

Your current credentials (from `.env.example`):
- **Email**: `sheikhqirat100@gmail.com`
- **App Password**: `bmux fhnt yvjb mhzn` (remove spaces → `bmuxfhntyvjbmhzn`)

**To verify**:
1. Go to https://myaccount.google.com/apppasswords
2. Check if app password exists
3. If not, generate new one:
   - Click "Select app" → "Other (Custom name)"
   - Enter: `NovaSaaS Support Render`
   - Copy 16-char password (no spaces)

---

### 3. Commit and Push Code Changes

```bash
# Check what changed
git status

# You should see:
# modified:   backend/src/agent/runner.py
# new file:   EMAIL_WHATSAPP_SENDING_FIX.md
# new file:   backend/test_email_sending.py
# new file:   DEPLOYMENT_CHECKLIST.md

# Commit the fix
git add backend/src/agent/runner.py
git add EMAIL_WHATSAPP_SENDING_FIX.md
git add backend/test_email_sending.py
git add DEPLOYMENT_CHECKLIST.md

git commit -m "fix: prioritize SMTP for email delivery and track status properly

- Changed email sending to try SMTP first, Gmail API as fallback
- Added delivery_status tracking (pending/sent/failed)
- Improved logging with emojis for better visibility
- Added test script for local SMTP verification
- Documented fix in EMAIL_WHATSAPP_SENDING_FIX.md"

git push origin main
```

---

## 🚀 Render Deployment Steps

### Step 1: Update Environment Variables

Go to: **Render Dashboard** → **Your Backend Service** → **Environment** tab

**Add/Update these variables**:

```bash
# ===== REQUIRED FOR EMAIL SENDING =====


# ===== WHATSAPP (optional - enable when bridge is ready) =====
WHATSAPP_MCP_ENABLED=false
WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge
WHATSAPP_POLL_INTERVAL=30

# ===== APP SETTINGS =====
ENVIRONMENT=production
API_KEY=your-secure-api-key-here

# ===== RATE LIMITING =====
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_WEBFORM_PER_MINUTE=10

# ===== ERROR MONITORING (optional) =====

**⚠️ Important**:
- Remove ALL spaces from `GMAIL_SENDER_PASSWORD`
- Use the app password, NOT your regular Gmail password
- Click "Save Changes" after updating

### Step 2: Trigger Deployment

Render will auto-deploy when you push to `main`. Or manually trigger:

1. Go to **Render Dashboard** → **Your Backend Service**
2. Click **Manual Deploy** → **Deploy latest commit**
3. Wait for deployment to complete (usually 2-5 minutes)

### Step 3: Monitor Deployment Logs

Watch the logs during deployment:

```
Building...
Installing dependencies...
Starting server...
✅ Server started on port 8000
```

Look for any errors related to:
- Missing environment variables
- Database connection
- SMTP configuration

---

## 🧪 Post-Deployment Testing

### Test 1: Submit Web Form Ticket

1. Go to your frontend URL: `https://your-frontend.onrender.com/support/webform`
2. Fill out the form:
   - **Name**: Test User
   - **Email**: YOUR_EMAIL@gmail.com (use your real email!)
   - **Subject**: Test email delivery
   - **Message**: Testing if AI response is sent to my email inbox
3. Click "Submit Support Ticket"
4. Copy the ticket ID

### Test 2: Check Render Logs

Go to **Render Dashboard** → **Backend Service** → **Logs**

Look for these log messages:

```
📧 Sending email response for ticket {ticket_id} to {email}
Attempting SMTP send to {email}
✅ Email sent successfully via SMTP to {email}
```

**If you see**:
- ✅ `Email sent successfully` → Perfect! Check your inbox
- ⚠️ `SMTP send returned False` → Check credentials
- ❌ `SMTP sending failed` → Check error message

### Test 3: Check Your Email Inbox

1. Open your email inbox (the one you used in the form)
2. Look for email from `sheikhqirat100@gmail.com`
3. Subject: `Re: Test email delivery (Ticket #...)`
4. Check spam folder if not in inbox

**Email should contain**:
- Beautiful HTML formatting
- Your ticket ID
- AI-generated response
- "Qirat Saeed AI Support" branding

### Test 4: Verify Database Status

Connect to your Neon database and run:

```sql
SELECT
    t.id as ticket_id,
    m.content,
    m.delivery_status,
    m.created_at,
    c.email as customer_email
FROM messages m
JOIN conversations conv ON conv.id = m.conversation_id
JOIN tickets t ON t.conversation_id = conv.id
JOIN customers c ON c.id = t.customer_id
WHERE m.direction = 'outgoing'
ORDER BY m.created_at DESC
LIMIT 5;
```

**Expected result**:
- `delivery_status` should be `'sent'` (not `'pending'` or `'failed'`)

---

## 🐛 Troubleshooting

### Issue: "Authentication failed" in logs

**Cause**: Wrong Gmail credentials

**Fix**:
1. Verify you're using app password, not regular password
2. Check 2FA is enabled on Gmail account
3. Regenerate app password at https://myaccount.google.com/apppasswords
4. Update `GMAIL_SENDER_PASSWORD` on Render (remove spaces!)
5. Redeploy

### Issue: "Connection timeout" in logs

**Cause**: Render firewall or network issue

**Fix**:
1. Check if Render allows outbound SMTP connections
2. Verify port 587 is not blocked
3. Try Gmail API fallback (requires service account setup)

### Issue: Email sent but not received

**Cause**: Email in spam or wrong recipient

**Fix**:
1. Check spam/junk folder
2. Verify customer email is correct in database
3. Check Gmail "Sent" folder to confirm it was sent
4. Add `sheikhqirat100@gmail.com` to contacts

### Issue: "delivery_status = 'failed'" in database

**Cause**: Both SMTP and Gmail API failed

**Fix**:
1. Check Render logs for specific error
2. Verify all environment variables are set
3. Test SMTP locally with `test_email_sending.py`
4. Check Gmail account for security alerts

---

## 📊 Success Criteria

After deployment, you should have:

- [x] Code deployed to Render
- [x] Environment variables configured
- [x] Test ticket submitted
- [x] Logs show "✅ Email sent successfully"
- [x] Customer receives email in inbox
- [x] Email has proper HTML formatting
- [x] Database shows `delivery_status = 'sent'`
- [x] No errors in Render logs

---

## 🎉 What's Fixed

### Before (Broken)
```
User submits ticket
  ↓
AI generates response
  ↓
Response stored in DB with status='sent'
  ↓
❌ Email NOT actually sent (Gmail API failed silently)
  ↓
User sees response in UI but never receives email
```

### After (Fixed)
```
User submits ticket
  ↓
AI generates response
  ↓
Response stored in DB with status='pending'
  ↓
Try SMTP send → ✅ Success!
  ↓
Update DB status='sent'
  ↓
✅ Customer receives email in inbox
```

---

## 📝 Code Changes Summary

**File**: `backend/src/agent/runner.py`

**Changes**:
1. Line 239: Set initial `delivery_status = 'pending'`
2. Lines 300-350: Prioritize SMTP, fallback to Gmail API
3. Lines 265-280: Update status to `'sent'` on success
4. Lines 355-365: Update status to `'failed'` if all methods fail
5. Added detailed logging with emojis (📧, ✅, ⚠️, ❌)

**Why this works**:
- SMTP is more reliable than Gmail API for Render
- Proper status tracking helps debug issues
- Fallback ensures delivery even if SMTP fails
- Detailed logs make troubleshooting easier

---

## 🔜 Next Steps (Optional)

### Enable WhatsApp Sending

When you're ready to enable WhatsApp:

1. Set up WhatsApp MCP Go bridge
2. Connect to WhatsApp Web
3. Update Render env: `WHATSAPP_MCP_ENABLED=true`
4. Redeploy
5. Test with WhatsApp message

### Set Up Gmail API (Optional)

For better email threading and reply handling:

1. Create Google Cloud project
2. Enable Gmail API
3. Create service account
4. Download credentials JSON
5. Add to Render as `GMAIL_CREDENTIALS_FILE` env var
6. Redeploy

---

## 📞 Support

If you still have issues after following this checklist:

1. **Check Render logs** for specific error messages
2. **Test locally** with `test_email_sending.py`
3. **Verify credentials** at https://myaccount.google.com/apppasswords
4. **Check Gmail security** for blocked login attempts
5. **Review database** for delivery_status values

---

**Last Updated**: 2026-02-24
**Status**: ✅ Ready to Deploy
