# WhatsApp Response Not Sending - Troubleshooting Guide

**Problem**: AI responses appear in frontend UI but not in WhatsApp app

**Root Cause**: WhatsApp MCP Go bridge not running or not authenticated

---

## Quick Fix (5 minutes)

### Step 1: Check if Go is Installed

```bash
go version
```

**If not installed**: Download from https://go.dev/dl/

### Step 2: Build WhatsApp Bridge

```bash
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge

# Build the bridge
go build -o whatsapp-bridge.exe main.go
```

**Windows Users**: If you get compiler errors, install MSYS2:
1. Download from https://www.msys2.org/
2. Install and open "UCRT64" terminal
3. Run: `pacman -S mingw-w64-ucrt-x86_64-gcc`
4. Try building again

### Step 3: Authenticate WhatsApp

```bash
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge

# Run the bridge
go run main.go
```

**You will see**:
- A QR code in the terminal
- Message: "Waiting for QR code scan..."

**On your phone**:
1. Open WhatsApp
2. Go to Settings → Linked Devices
3. Tap "Link a Device"
4. Scan the QR code on your computer screen

**After scanning**:
- Terminal will show "Authenticated!"
- Database files created in `store/` directory
- Bridge starts listening on http://localhost:8080

**Keep this terminal window open!** The bridge must run continuously.

### Step 4: Test the Integration

```bash
cd D:\Hackathon_05\backend

# Run the test script
python test_whatsapp_flow.py
```

**Expected output**:
```
✅ Bridge executable found
✅ Database found
✅ MCP client initialized
✅ Go bridge appears to be available
✅ Message sent successfully!
```

Check your WhatsApp - you should receive a test message!

### Step 5: Start the Backend

**In a NEW terminal** (keep bridge running in the first one):

```bash
cd D:\Hackathon_05\backend

# Start the message processor worker
python -m src.workers.message_processor
```

**In a THIRD terminal**:

```bash
cd D:\Hackathon_05\backend

# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Test End-to-End

**Option A: Via Webhook**
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp/mcp ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\": \"+923082931005\", \"message\": \"Hello\"}"
```

**Option B: Via Frontend**
1. Open http://localhost:3000/support
2. Submit a ticket (this goes via web_form, not WhatsApp)
3. For WhatsApp testing, use the webhook method above

---

## Architecture Overview

```
Customer sends WhatsApp message
        ↓
Go bridge receives it (whatsapp-bridge.exe)
        ↓
Stores in SQLite (messages.db)
        ↓
WhatsApp Worker polls every 30s
        ↓
Creates ticket + publishes to Kafka
        ↓
Message Processor consumes Kafka
        ↓
AI Agent generates response
        ↓
WhatsApp Handler sends via Go bridge
        ↓
Go bridge sends to WhatsApp servers
        ↓
Customer receives response ✅
```

---

## Common Issues

### Issue 1: "Go bridge executable not found"

**Solution**:
```bash
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge
go build -o whatsapp-bridge.exe main.go
```

### Issue 2: "Database not found"

**Cause**: Bridge hasn't been authenticated yet

**Solution**:
1. Run `go run main.go`
2. Scan QR code with WhatsApp
3. Wait for "Authenticated!" message

### Issue 3: "Connection refused" or "Cannot connect to bridge"

**Cause**: Go bridge is not running

**Solution**:
1. Open a terminal
2. Navigate to bridge directory
3. Run `go run main.go`
4. Keep terminal open

### Issue 4: Messages stored but not sent

**Check logs for**:
```
WhatsApp MCP not initialized, message stored in DB only
```

**Solution**:
1. Make sure bridge is running BEFORE starting backend
2. Check `WHATSAPP_MCP_ENABLED=true` in `.env`
3. Restart the message processor worker

### Issue 5: QR code won't appear

**Solution**:
```bash
# Delete old session and re-authenticate
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge
rm -rf store/
go run main.go
```

### Issue 6: "Authentication expired"

**Cause**: WhatsApp session expires after ~20 days

**Solution**:
1. Stop the bridge (Ctrl+C)
2. Delete `store/` directory
3. Re-run `go run main.go`
4. Scan QR code again

---

## Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. Check bridge executable exists
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge
dir whatsapp-bridge.exe

# 2. Check database exists
dir store\messages.db

# 3. Check bridge is running (in another terminal)
curl http://localhost:8080/api/status

# 4. Test API endpoint
curl http://localhost:8000/webhooks/whatsapp/status

# 5. Run integration test
cd D:\Hackathon_05\backend
python test_whatsapp_flow.py
```

---

## Process Setup (Development)

You need **3 terminal windows**:

### Terminal 1: Go Bridge (Always Running)
```bash
cd D:\Hackathon_05\backend\whatsapp-mcp\whatsapp-bridge
go run main.go
```

### Terminal 2: Message Processor Worker
```bash
cd D:\Hackathon_05\backend
python -m src.workers.message_processor
```

### Terminal 3: API Server
```bash
cd D:\Hackathon_05\backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Optional Terminal 4: Frontend**
```bash
cd D:\Hackathon_05\frontend
npm run dev
```

---

## Logs to Watch

### When WhatsApp message arrives:
```
INFO: Processing message from fte.channels.whatsapp.inbound
INFO: Ticket: abc-123, Customer: def-456, Channel: whatsapp
INFO: Sentiment score: 0.1 (NEGATIVE)
INFO: Agent response generated for ticket abc-123
INFO: Sending response via WhatsApp MCP for ticket abc-123
INFO: WhatsApp handler initialized: True
INFO: WhatsApp MCP response sent: True to +923082931005
```

### If bridge not running:
```
WARNING: WhatsApp MCP not initialized, message stored in DB only
WARNING: Start the Go bridge: cd whatsapp-mcp/whatsapp-bridge && go run main.go
```

### If MCP disabled:
```
INFO: WhatsApp MCP disabled in settings, message stored in DB only
INFO: To enable, set WHATSAPP_MCP_ENABLED=true in .env
```

---

## Configuration Reference

### backend/.env
```env
# MUST be set to true
WHATSAPP_MCP_ENABLED=true

# Path to bridge directory
WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge

# How often to poll for new messages (seconds)
WHATSAPP_POLL_INTERVAL=30
```

### src/config.py
```python
whatsapp_mcp_enabled: bool = True  # Default is now True
```

---

## Testing Scenarios

### Test 1: Send WhatsApp Message
1. Send message from your WhatsApp to the linked number
2. Check backend logs for ticket creation
3. Verify AI response appears in your WhatsApp

### Test 2: Check Database
```bash
cd D:\Hackathon_05\backend
python -c "from src.channels.whatsapp_mcp_client import WhatsAppMCPClient; import asyncio; client = WhatsAppMCPClient('./whatsapp-mcp/whatsapp-bridge'); asyncio.run(client.initialize()); msgs = asyncio.run(client._db_client.get_unread_messages()); print(f'Unread messages: {len(msgs)}')"
```

### Test 3: Manual Send
```bash
cd D:\Hackathon_05\backend
python -c "from src.channels.whatsapp_mcp_client import WhatsAppMCPClient; import asyncio; client = WhatsAppMCPClient('./whatsapp-mcp/whatsapp-bridge'); asyncio.run(client.initialize()); success = asyncio.run(client.send_message('+923082931005', 'Test message')); print(f'Sent: {success}')"
```

---

## Production Notes

**Current Setup**: Development only (unofficial WhatsApp Web API)

**For Production**:
1. Use **Twilio WhatsApp API** (official)
2. See `GMAIL_AND_WEBFORM_STATUS.md` for Twilio integration status
3. Requires business verification with Meta

---

## Summary

**To fix your issue**:

1. ✅ **Start Go bridge**: `cd whatsapp-mcp/whatsapp-bridge && go run main.go`
2. ✅ **Scan QR code** with WhatsApp mobile app
3. ✅ **Keep bridge running** in background
4. ✅ **Start message processor**: `python -m src.workers.message_processor`
5. ✅ **Test with script**: `python test_whatsapp_flow.py`

**Expected Result**: AI responses will be sent to WhatsApp app within 30 seconds.

---

**Questions?** Check logs for detailed error messages.
