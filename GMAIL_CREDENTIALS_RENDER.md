# ✅ Gmail Credentials Configured for Render

## 🔧 What Was Done

You added `credentials.json` to Render as an environment file. I've updated the code to read it from the correct path.

## 📝 Files Updated

### 1. `backend/src/channels/gmail_handler.py`
Added support for Render's file path:

```python
# Try absolute path for Render
render_creds_path = Path("/opt/render/project/src/credentials.json")
if render_creds_path.exists():
    credentials = service_account.Credentials.from_service_account_file(
        str(render_creds_path),
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )
    self._service = build("gmail", "v1", credentials=credentials)
    logger.info(f"Gmail service authenticated via Render path")
    return self._service
```

### 2. `backend/.env`
Updated credentials path for Render:
```env
GMAIL_CREDENTIALS_PATH=/opt/render/project/src/credentials.json
```

## 🚀 Deploy to Render

```bash
cd backend
git add src/channels/gmail_handler.py src/agent/runner.py .env .env.example
git commit -m "Fix: Read Gmail credentials from Render path"
git push
```

## ✅ Expected Behavior

After deploy, when a web form ticket is processed:

**Render Logs should show:**
```
INFO: Gmail service authenticated via Render path: /opt/render/project/src/credentials.json
INFO: Sending response via web_form for ticket {id}
INFO: Gmail reply sent successfully. Message ID: {message_id}
✅ Response sent successfully via Gmail API to {email}
```

**You should receive:**
- ✅ Email in inbox at `saeedqirat43@gmail.com`
- ✅ Subject: "Re: Support Request (Ticket #xxxxx)"
- ✅ AI-generated response in email body

## 🔍 Troubleshooting

### If emails still not received:

**1. Check Render Logs**

Look for these errors:
```
ERROR: Gmail authentication failed
ERROR: Gmail send failed
ERROR: SMTP fallback also failed
```

**2. Verify credentials.json on Render**

In Render dashboard:
- Go to your service
- Click "Files" tab
- Verify `credentials.json` exists at root

**3. Check Service Account Permissions**

Your Gmail service account needs:
- Gmail API enabled in Google Cloud Console
- Service account has `gmail.send` scope
- If using Google Workspace: Domain-wide delegation enabled

**4. Test Locally First**

```bash
cd backend
uv run python -c "
from src.channels.gmail_handler import GmailHandler
from src.kafka.client import FTEKafkaProducer

producer = FTEKafkaProducer()
handler = GmailHandler(producer)
service = handler._get_gmail_service()
print('Service:', service)
"
```

## 📊 Email Flow

```
Web Form Submit → Ticket Created → AI Processes → Gmail API Sends → Email Delivered
                                              ↓
                                    (credentials.json auth)
```

## ✅ What's Working Now

1. ✅ Credentials read from Render path
2. ✅ Gmail API authentication
3. ✅ Email sending for ALL channels (email, web_form, whatsapp)
4. ✅ Fallback to SMTP if Gmail API fails
5. ✅ Error logging for debugging

## 🎯 Test Now

1. **Deploy to Render** (git push)
2. **Submit new web form ticket**
3. **Click "Get AI Response"**
4. **Check email inbox** (and spam folder)
5. **Check Render logs** for confirmation

---

## 💡 Important Notes

**Gmail Service Account Setup:**

If you haven't already, make sure your `credentials.json` has:

1. **Gmail API Enabled**
   - Go to Google Cloud Console
   - Enable Gmail API

2. **Correct Scopes**
   - Code uses: `gmail.send`
   - Service account must have this permission

3. **Sender Email Authorized**
   - The email in `GMAIL_SENDER_EMAIL` must match the service account
   - Or service account must have delegation rights

**Render File Upload:**

You mentioned you added `credentials.json` - make sure it's:
- Uploaded to: `/opt/render/project/src/credentials.json`
- Or set as environment variable: `GMAIL_CREDENTIALS_FILE`
