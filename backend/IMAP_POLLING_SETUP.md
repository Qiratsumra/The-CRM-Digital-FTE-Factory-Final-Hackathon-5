# IMAP Polling Setup Guide - Receive Emails Without Domain Delegation

## Overview

**IMAP Polling** is a workaround that allows you to receive emails in your Customer Success FTE **without requiring Google Workspace domain-wide delegation**.

Instead of using the Gmail API (which requires admin approval), IMAP polling connects directly to Gmail's IMAP server using your app password.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMAP Polling Architecture                     │
│                                                                  │
│  1. Customer sends email to support@yourcompany.com             │
│         ↓                                                        │
│  2. Email arrives in Gmail inbox                                │
│         ↓                                                        │
│  3. IMAP Poller checks inbox every 60 seconds                   │
│         ↓                                                        │
│  4. New email detected → Create ticket in database              │
│         ↓                                                        │
│  5. AI agent processes email and generates response             │
│         ↓                                                        │
│  6. Response sent via Gmail SMTP                                │
│         ↓                                                        │
│  7. Email marked as read in Gmail                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comparison: IMAP vs Gmail API

| Feature | Gmail API | IMAP Polling |
|---------|-----------|--------------|
| **Setup Complexity** | High (requires admin) | Low (any Gmail account) |
| **Google Workspace** | Required | Not required |
| **Domain Delegation** | Required | Not required |
| **Real-time** | Yes (Pub/Sub push) | No (polling delay) |
| **Latency** | Instant | 30-60 seconds |
| **Authentication** | OAuth 2.0 / Service Account | App password |
| **Best For** | Production | Development / Small teams |

---

## Prerequisites

1. **Gmail Account** - Any Gmail account (personal or business)
2. **IMAP Enabled** - IMAP must be enabled in Gmail settings
3. **App Password** - 16-character app password from Google

---

## Step-by-Step Setup

### Step 1: Enable IMAP in Gmail

1. Go to [Gmail Settings](https://mail.google.com/mail/u/0/#settings/fwdandpop)
2. Click **"See all settings"**
3. Go to **"Forwarding and POP/IMAP"** tab
4. Under **"IMAP Access"**, select **"Enable IMAP"**
5. Click **"Save Changes"**

![Enable IMAP](https://i.imgur.com/example1.png)

---

### Step 2: Enable 2-Factor Authentication

Google requires 2FA for app passwords:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under **"Signing in to Google"**, click **"2-Step Verification"**
3. Follow the setup process
4. Enable 2-Step Verification

---

### Step 3: Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **"Mail"** and **"Other (Custom name)"**
3. Enter **"Customer Success FTE"** as the name
4. Click **"Generate"**
5. Copy the 16-character password (save it securely)

```
Example: abcd efgh ijkl mnop
```

**Important:** This is a one-time display. Save it immediately!

---

### Step 4: Configure Environment Variables

Add to your `backend/.env` file:

```env
# Gmail SMTP (for sending)
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_SENDER_PASSWORD="abcd efgh ijkl mnop"  # App password (no spaces: abcdefghijklmnop)

# IMAP Polling (for receiving)
IMAP_POLL_INTERVAL=60  # Poll every 60 seconds

# Optional: Disable Gmail API if using IMAP only
GMAIL_API_ENABLED=false
```

---

### Step 5: Run the IMAP Poller

#### Option A: Run Once (Testing)

```bash
cd backend
uv run python -m src.channels.imap_poller --once
```

**Output:**
```
INFO: Connected to Gmail IMAP: your-email@gmail.com
INFO: Found 3 new email(s)
INFO: Created ticket abc123 from email: How do I reset...
INFO: Processed 3 email(s)
Processed 3 email(s)
```

#### Option B: Run Continuously (Production)

```bash
cd backend
uv run python -m src.channels.imap_poller --interval 60
```

**Output:**
```
INFO: Starting continuous IMAP polling (interval: 60s)
INFO: Connected to Gmail IMAP: your-email@gmail.com
INFO: No new emails found
INFO: No new emails found
INFO: Found 1 new email(s)
INFO: Created ticket def456 from email: API question...
```

#### Option C: Run as Background Worker

Add to your `docker-compose.yml`:

```yaml
services:
  imap-poller:
    build: ./backend
    env_file:
      - ./backend/.env
    command: python -m src.channels.imap_poller --interval 60
    volumes:
      - ./backend:/app
      - imap_state:/app/imap_state  # Persist state

volumes:
  imap_state:
```

Then run:

```bash
docker compose up -d imap-poller
```

---

## How It Works (Technical Details)

### 1. Connection

```python
import imaplib

# Connect to Gmail IMAP server
mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)

# Login with app password
mail.login("your-email@gmail.com", "app-password")

# Select inbox
mail.select("inbox")
```

### 2. Search for New Emails

```python
# Get unread emails
_, message_data = mail.uid("search", None, "UNSEEN")

# Or get emails since last UID
_, message_data = mail.uid("search", None, f"UID {last_uid}:*")
```

### 3. Fetch and Parse Email

```python
import email

# Fetch email by UID
_, msg_data = mail.uid("fetch", uid, "(RFC822)")

# Parse email
msg = email.message_from_bytes(raw_email)

# Extract headers
from_address = msg.get("From")
subject = msg.get("Subject")

# Get body
if msg.is_multipart():
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode()
```

### 4. Create Ticket and Process

```python
# Create customer
customer_id = await queries.create_customer(pool, email=from_address)

# Create ticket
ticket_id = await queries.create_ticket(pool, customer_id=customer_id, ...)

# Publish to Kafka
await producer.publish(TOPICS["email_inbound"], {...})

# Mark as read
mail.uid("STORE", uid, "+FLAGS", "\\Seen")
```

### 5. Send Reply (via SMTP)

```python
import smtplib
from email.mime.multipart import MIMEMultipart

# Create message
msg = MIMEMultipart()
msg["Subject"] = f"Re: {subject}"
msg["From"] = "your-email@gmail.com"
msg["To"] = customer_email

# Send via Gmail SMTP
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("your-email@gmail.com", "app-password")
    server.send_message(msg)
```

---

## State Management

The poller tracks processed emails using a state file:

```
backend/imap_state.pkl
```

This file stores:
- Last processed UID
- Prevents duplicate processing
- Survives restarts

**Reset State (re-process all emails):**

```bash
rm imap_state.pkl
```

---

## Troubleshooting

### Error: "Invalid credentials"

**Cause:** Wrong app password or 2FA not enabled

**Solution:**
1. Verify 2FA is enabled
2. Generate new app password
3. Update `.env` with new password

---

### Error: "IMAP connection failed"

**Cause:** IMAP not enabled in Gmail

**Solution:**
1. Go to Gmail settings
2. Enable IMAP in "Forwarding and POP/IMAP"
3. Save changes

---

### Error: "No new emails found" (but you sent one)

**Cause:** Email already marked as read

**Solution:**
1. Send a new email (make sure it's unread)
2. Or reset state: `rm imap_state.pkl`
3. Poller will process all unread emails on first run

---

### Error: "Too many login attempts"

**Cause:** Polling too frequently

**Solution:**
1. Increase poll interval: `IMAP_POLL_INTERVAL=120`
2. Gmail allows ~15 IMAP connections per hour

---

### Emails Not Being Processed

**Check:**
1. Poller is running (`ps aux | grep imap_poller`)
2. Logs show no errors
3. State file exists and is writable
4. Emails are unread (not already processed)

---

## Production Considerations

### 1. Polling Interval

**Recommendation:** 60-120 seconds

- Shorter interval = faster response but more API calls
- Gmail rate limit: ~15 IMAP connections per hour
- For 24/7 polling, use 60+ seconds

---

### 2. Multiple Instances

**Problem:** Running multiple pollers causes duplicate processing

**Solution:** Use distributed lock or single instance:

```python
# Use Redis for distributed lock
from redis import Redis

redis = Redis()

async def poll_once():
    # Try to acquire lock
    if redis.set("imap_poll_lock", "1", nx=True, ex=60):
        await poller.poll_once()
```

---

### 3. Error Handling

The poller includes retry logic:

```python
try:
    await poller.poll_once()
except Exception as e:
    logger.error(f"Polling error: {e}")
    await asyncio.sleep(30)  # Wait before retry
```

---

### 4. Monitoring

Add metrics:

```python
# Track polling metrics
await queries.create_metric(
    pool,
    metric_name="imap_poll_count",
    metric_value=processed_count,
    channel="email",
)
```

---

## Integration with Existing System

The IMAP poller integrates seamlessly with your existing Customer Success FTE:

1. **Same Database** - Uses existing `customers`, `tickets`, `messages` tables
2. **Same Kafka Topics** - Publishes to `email_inbound` topic
3. **Same AI Agent** - Uses existing `AgentRunner` for processing
4. **Same SMTP** - Sends replies via Gmail SMTP

**No changes needed to existing code!**

---

## Testing

### Test 1: Send Test Email

```bash
# From another email account
echo "Test email body" | mail -s "Test Subject" your-email@gmail.com
```

### Test 2: Run Poller

```bash
cd backend
uv run python -m src.channels.imap_poller --once
```

### Test 3: Check Database

```sql
SELECT * FROM tickets ORDER BY created_at DESC LIMIT 1;
```

### Test 4: Check Logs

```
INFO: Created ticket abc123 from email: Test Subject
INFO: Processed 1 email(s)
```

---

## Migration from Gmail API

If you're currently using Gmail API and want to switch to IMAP:

### 1. Stop Gmail API Worker

```bash
# Stop the Gmail webhook processor
docker compose stop worker
```

### 2. Update Configuration

```env
# Disable Gmail API
GMAIL_API_ENABLED=false

# Enable IMAP polling
IMAP_POLL_INTERVAL=60
```

### 3. Start IMAP Poller

```bash
docker compose up -d imap-poller
```

### 4. Verify

Check that new emails are being processed via IMAP.

---

## Security Best Practices

1. **Use App Password** - Never use your regular Gmail password
2. **Restrict IP** - If possible, restrict IMAP access to your server IP
3. **Monitor Logs** - Watch for failed login attempts
4. **Rotate Password** - Change app password periodically
5. **Use HTTPS** - IMAP over SSL (port 993) is already encrypted

---

## Limitations

1. **Not Real-time** - 30-60 second delay vs instant with Pub/Sub
2. **Single Inbox** - Can only poll one email address
3. **Rate Limits** - Gmail IMAP has connection limits
4. **No Push** - Must poll continuously (uses some resources)

---

## When to Use IMAP vs Gmail API

### Use IMAP Polling If:
- ✅ You don't have Google Workspace
- ✅ You're in development/testing
- ✅ You need quick setup
- ✅ 30-60 second delay is acceptable

### Use Gmail API If:
- ✅ You have Google Workspace
- ✅ You need real-time processing
- ✅ You're in production
- ✅ You need advanced features (labels, filters, etc.)

---

## Summary

**IMAP Polling** provides a simple, effective workaround for receiving emails without Google Workspace domain delegation.

**Setup Time:** 5-10 minutes
**Complexity:** Low
**Reliability:** High
**Latency:** 30-60 seconds

**Perfect for:**
- Hackathon demos
- Development environments
- Small teams without Google Workspace
- Quick prototypes

---

## Quick Start Commands

```bash
# 1. Enable IMAP in Gmail (one-time)
# https://myaccount.google.com/lesssecureapps

# 2. Generate app password
# https://myaccount.google.com/apppasswords

# 3. Update .env
echo "GMAIL_SENDER_EMAIL=your-email@gmail.com" >> .env
echo "GMAIL_SENDER_PASSWORD=your-app-password" >> .env
echo "IMAP_POLL_INTERVAL=60" >> .env

# 4. Run poller
uv run python -m src.channels.imap_poller --interval 60
```

**That's it!** Your system will now receive emails automatically.
