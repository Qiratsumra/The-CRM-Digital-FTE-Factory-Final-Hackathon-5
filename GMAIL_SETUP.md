# Gmail Setup Guide

## Configure Gmail for Sending Emails

The system uses Gmail SMTP to send AI responses to customers. Follow these steps to set it up:

### 1. Enable 2-Factor Authentication (Required)

1. Go to your Google Account: https://myaccount.google.com/
2. Click on **Security** in the left sidebar
3. Under "Signing in to Google", click **2-Step Verification**
4. Follow the steps to enable 2FA

### 2. Generate App Password

1. Go to: https://myaccount.google.com/apppasswords
2. If prompted, sign in again
3. Under "App passwords", click **Select app** → **Other (Custom name)**
4. Enter: `NovaSaaS Support`
5. Click **Generate**
6. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### 3. Update .env File

Open `backend/.env` and add your credentials:

```env
GMAIL_SENDER_EMAIL=sheikhqirat100@gmail.com
GMAIL_SENDER_PASSWORD=abcdefghijklmnop  # 16-char app password (no spaces)
SUPPORT_TEAM_EMAIL=sheikhqirat100@gmail.com
```

**Important:**
- Use the **app password**, NOT your regular Gmail password
- Remove spaces from the app password
- Keep this file secure and never commit it to Git

### 4. Test the Configuration

Restart the backend server:

```bash
cd backend
uvicorn src.api.main:app --reload
```

Submit a test ticket and verify you receive an email response.

---

## Troubleshooting

### "Authentication failed" error

- Make sure you're using the **app password**, not your regular password
- Check that 2FA is enabled on your Google account
- Verify the email address matches your Google account

### "Connection timeout" error

- Check your internet connection
- Gmail SMTP server: `smtp.gmail.com`
- Port: `587` (TLS)

### Email not sending

- Check backend logs for errors
- Verify `GMAIL_SENDER_EMAIL` and `GMAIL_SENDER_PASSWORD` are set
- Make sure the customer email is valid

---

## Email Features

### What Gets Sent

When a ticket is submitted via web form and processed by AI:

1. **Customer receives**: Beautiful HTML email with AI response
2. **Support team receives**: Notification if ticket is escalated

### Email Template

The email includes:
- Ticket ID and subject
- AI-generated response
- Professional formatting with NovaSaaS branding
- Links to view ticket status

### Escalation Notifications

If a ticket is escalated (angry customer, legal request, etc.), the support team receives an email with:
- Ticket details
- Escalation reason
- Full message history

---

## Security Notes

- **Never** commit `.env` file to version control
- Use app passwords instead of regular passwords
- Rotate app passwords periodically
- Monitor Gmail account for suspicious activity
