# WhatsApp Integration Testing Guide

**Date**: 2026-03-05  
**Status**: ⚠️ Bridge Not Running

---

## 🔍 Current Status

### Configuration (backend/.env)
```env
WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge
WHATSAPP_MCP_ENABLED=true
WHATSAPP_POLL_INTERVAL=30
```

### Bridge Status
```
❌ WhatsApp bridge NOT running on http://localhost:8080
Error: Connection refused
```

---

## 📋 WhatsApp Architecture

```
Your Phone (WhatsApp)
    ↓ QR Code Scan
WhatsApp Bridge (Go - port 8080)
    ↓ SQLite Database
MCP Client (Python)
    ↓ Kafka
AI Agent
    ↓
Backend API
    ↓
Frontend
```

---

## 🚀 Step-by-Step Testing

### Step 1: Check Bridge Executable

```bash
# Check if bridge executable exists
dir backend\whatsapp-mcp\whatsapp-bridge\whatsapp-bridge.exe
```

**Expected**: File exists (already compiled)

**If missing**:
```bash
cd backend\whatsapp-mcp\whatsapp-bridge
go env -w CGO_ENABLED=1
go build -o whatsapp-bridge.exe main.go
```

---

### Step 2: Start WhatsApp Bridge

```bash
cd backend\whatsapp-mcp\whatsapp-bridge
.\whatsapp-bridge.exe
```

**First Time Setup**:
1. QR code will display in terminal
2. Open WhatsApp on your phone
3. Go to: Settings → Linked Devices → Link a Device
4. Scan the QR code
5. Wait for "Authenticated!" message

**Subsequent Runs**:
- Bridge auto-reconnects (no QR needed)
- Session lasts ~20 days

**Keep Running**: The bridge must stay running for WhatsApp to work!

---

### Step 3: Verify Bridge is Running

```bash
# Test bridge API
curl -X POST http://localhost:8080/api/send ^
  -H "Content-Type: application/json" ^
  -d "{\"recipient\": \"+923001234567\", \"message\": \"Test\"}"
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Message sent"
}
```

**If Connection Refused**:
- Bridge is not running
- Check terminal for errors
- Ensure port 8080 is not blocked

---

### Step 4: Check Database

```bash
# WhatsApp messages stored in SQLite
dir backend\whatsapp-mcp\whatsapp-bridge\store\messages.db
```

**Expected**: File exists and grows as messages arrive

---

### Step 5: Test WhatsApp Message Sending

#### Option A: Via API Endpoint

```bash
# Send test message to your WhatsApp
curl -X POST http://localhost:8080/api/send ^
  -H "Content-Type: application/json" ^
  -d "{\"recipient\": \"+923001234567\", \"message\": \"Hello from Customer Success FTE!\"}"
```

**Check your WhatsApp**: You should receive the message

#### Option B: Via Backend Endpoint

```bash
# Submit ticket via WhatsApp webhook
curl -X POST http://localhost:8000/webhooks/whatsapp/mcp ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\": \"+923001234567\", \"message\": \"I need help with...\"}"
```

**Expected**: Returns `ticket_id`

---

### Step 6: Test Full Flow

#### 1. Start All Services

**Terminal 1 - WhatsApp Bridge**:
```bash
cd backend\whatsapp-mcp\whatsapp-bridge
.\whatsapp-bridge.exe
```

**Terminal 2 - Backend**:
```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend** (optional):
```bash
cd frontend
npm run dev
```

#### 2. Send WhatsApp Message

From your WhatsApp, send a message to the linked number.

#### 3. Check Backend Logs

Look for:
```
INFO: Processed WhatsApp message from +923001234567
INFO: Sentiment score: 0.58 (neutral)
INFO: 📧 Sending email response... (or WhatsApp via MCP)
```

---

## 🧪 Test Commands

### 1. Check Bridge Status

```bash
curl http://localhost:8080/api/health
```

**Expected**: Bridge health response

### 2. List Contacts

```bash
curl http://localhost:8080/api/contacts
```

**Expected**: List of WhatsApp contacts

### 3. Send Message

```bash
curl -X POST http://localhost:8080/api/send ^
  -H "Content-Type: application/json" ^
  -d "{\"recipient\": \"+923001234567\", \"message\": \"Test message\"}"
```

### 4. Get Recent Messages

```bash
curl "http://localhost:8080/api/messages?chat_jid=923001234567@s.whatsapp.net&limit=10"
```

---

## 🐛 Troubleshooting

### Bridge Won't Start

**Error**: `Binary was compiled with 'CGO_ENABLED=0'`

**Fix**:
```bash
cd backend\whatsapp-mcp\whatsapp-bridge
go env -w CGO_ENABLED=1
go build -o whatsapp-bridge.exe main.go
.\whatsapp-bridge.exe
```

**Error**: `port 8080 already in use`

**Fix**:
```bash
# Find and kill process using port 8080
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### QR Code Not Showing

**Possible causes**:
1. Terminal doesn't support QR codes
2. Already authenticated (check logs)
3. WhatsApp session expired

**Fix**:
```bash
# Delete session and re-authenticate
del backend\whatsapp-mcp\whatsapp-bridge\store\messages.db
del backend\whatsapp-mcp\whatsapp-bridge\store\whatsapp.db
.\whatsapp-bridge.exe
```

### Messages Not Sending

**Check**:
1. Bridge is running (port 8080)
2. Phone number format is correct (E.164: +923001234567)
3. WhatsApp account is linked
4. Check bridge logs for errors

**Test manually**:
```bash
curl -X POST http://localhost:8080/api/send ^
  -H "Content-Type: application/json" ^
  -d "{\"recipient\": \"+923001234567\", \"message\": \"Test\"}"
```

### Backend Not Receiving Messages

**Issue**: WhatsApp MCP polls database for new messages

**Check**:
1. `WHATSAPP_MCP_ENABLED=true` in `.env`
2. Bridge is running and authenticated
3. Messages are in database:
   ```bash
   # Check messages.db exists
   dir backend\whatsapp-mcp\whatsapp-bridge\store\messages.db
   ```

---

## 📊 WhatsApp Integration Checklist

### Prerequisites
- [ ] Go installed (`go version`)
- [ ] WhatsApp account on phone
- [ ] Phone can receive messages

### Setup
- [ ] Bridge executable exists
- [ ] Bridge compiled with CGO enabled (Windows)
- [ ] QR code scanned and authenticated
- [ ] Bridge running on port 8080

### Configuration
- [ ] `WHATSAPP_MCP_ENABLED=true` in backend/.env
- [ ] `WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge`
- [ ] `WHATSAPP_POLL_INTERVAL=30`

### Testing
- [ ] Bridge responds on http://localhost:8080
- [ ] Can send message via bridge API
- [ ] Can receive message from WhatsApp
- [ ] Backend processes WhatsApp webhook
- [ ] AI response sent back via WhatsApp

### Production (Optional)
- [ ] Bridge deployed to same server as backend
- [ ] Bridge runs as background service
- [ ] Session backed up (store/ folder)
- [ ] Monitoring for bridge crashes

---

## 🎯 Quick Test Script

Create `test_whatsapp.py`:

```python
"""Test WhatsApp integration."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.channels.whatsapp_mcp_client import WhatsAppMCPClient

async def test_whatsapp():
    # Your WhatsApp number (with country code, no +)
    test_phone = "923001234567"  # Replace with your number
    test_message = "Hello! This is a test from Customer Success FTE."
    
    print("=" * 60)
    print("WhatsApp Integration Test")
    print("=" * 60)
    
    # Initialize client
    client = WhatsAppMCPClient(bridge_path="./backend/whatsapp-mcp/whatsapp-bridge")
    
    print("\n1. Checking bridge status...")
    bridge_exists = await client.check_go_bridge_status()
    print(f"   Bridge executable: {'✅' if bridge_exists else '❌'}")
    
    print("\n2. Initializing MCP client...")
    initialized = await client.initialize()
    print(f"   MCP client: {'✅' if initialized else '❌'}")
    
    if not initialized:
        print("\n   ⚠️ Make sure WhatsApp bridge is running!")
        print("   cd backend/whatsapp-mcp/whatsapp-bridge")
        print("   ./whatsapp-bridge.exe")
        return
    
    print("\n3. Sending test message...")
    success = await client.send_message(test_phone, test_message)
    print(f"   Message sent: {'✅' if success else '❌'}")
    
    print("\n4. Checking for incoming messages...")
    message = await client.receive_message(test_phone)
    if message:
        print(f"   Found message: {message.message_text[:50]}...")
    else:
        print("   No new messages")
    
    await client.close()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_whatsapp())
```

Run: `python test_whatsapp.py`

---

## 📝 Phone Number Format

WhatsApp requires **E.164 format**:

| Format | Example | Valid |
|--------|---------|-------|
| International | `+923001234567` | ✅ |
| Without + | `923001234567` | ✅ |
| Local with 0 | `03001234567` | ⚠️ Auto-converted |
| Without country code | `03001234567` | ⚠️ Auto-converted |

**Auto-conversion** (handled by code):
- `03001234567` → `923001234567`
- `3001234567` → `923001234567`

---

## 🔗 Integration Points

### 1. Inbound Messages (WhatsApp → Backend)

```
WhatsApp Message
    ↓
Bridge (polls WhatsApp Web)
    ↓ SQLite
MCP Client (polls database)
    ↓
WhatsApp Handler
    ↓ Kafka
AI Agent
    ↓
Database (ticket created)
```

### 2. Outbound Messages (Backend → WhatsApp)

```
AI Response Generated
    ↓
WhatsApp Handler
    ↓ MCP Client
Bridge API (POST /api/send)
    ↓
WhatsApp Web API
    ↓
Customer's WhatsApp
```

---

## ✅ Success Criteria

- [ ] Bridge starts without errors
- [ ] QR code scanned successfully
- [ ] Bridge stays connected
- [ ] Can send messages via API
- [ ] Can receive messages from WhatsApp
- [ ] Backend processes WhatsApp tickets
- [ ] AI responses sent via WhatsApp
- [ ] Response truncated to ≤300 chars

---

## 🚀 Next Steps

1. **Start Bridge**: `cd backend\whatsapp-mcp\whatsapp-bridge && .\whatsapp-bridge.exe`
2. **Scan QR Code** with WhatsApp phone
3. **Test Sending**: Use curl or test script
4. **Submit Ticket**: Via WhatsApp message
5. **Check Response**: AI response on WhatsApp

---

**Status**: ⚠️ Bridge not running - start it to test  
**Time Required**: ~5 minutes for first setup  
**Documentation**: See `backend/whatsapp-mcp/README.md`
