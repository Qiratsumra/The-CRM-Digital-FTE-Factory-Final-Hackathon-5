# WhatsApp MCP Integration Guide

**Date**: 2026-02-21  
**Status**: ✅ **IMPLEMENTED**

---

## Executive Summary

This guide explains how to integrate **WhatsApp MCP** (from [`lharries/whatsapp-mcp`](https://github.com/lharries/whatsapp-mcp)) with the **Customer Success FTE** system for real-time WhatsApp messaging.

### What's Implemented

✅ **WhatsApp MCP Client** - Direct SQLite database access  
✅ **WhatsApp Handler** - Channel handler for message processing  
✅ **API Endpoints** - Webhook for incoming messages  
✅ **Worker** - Background polling for new messages  
✅ **Agent Integration** - AI responses sent via WhatsApp MCP  

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER SUCCESS FTE                          │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   FastAPI    │────▶│  WhatsApp    │────▶│   WhatsApp   │   │
│  │   Endpoints  │     │   Handler    │     │   MCP Client │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│         │                                       │               │
│         ▼                                       ▼               │
│  ┌──────────────┐                       ┌──────────────┐       │
│  │    Kafka     │                       │   SQLite DB  │       │
│  │   (Queue)    │                       │ (messages.db)│       │
│  └──────────────┘                       └──────────────┘       │
│         │                                       │               │
│         ▼                                       ▼               │
│  ┌──────────────┐                       ┌──────────────┐       │
│  │  AI Agent    │                       │  Go Bridge   │       │
│  │  (Gemini)    │                       │ (whatsmeow)  │       │
│  └──────────────┘                       └──────────────┘       │
│                                                 │               │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                                                  ▼
                                         ┌──────────────┐
                                         │  WhatsApp    │
                                         │  Web API     │
                                         └──────────────┘
```

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Go** | 1.21+ | WhatsApp bridge compilation |
| **Python** | 3.14+ | Backend runtime |
| **UV** | Latest | Python package manager |
| **Git** | Latest | Clone repositories |

### WhatsApp MCP Repository

Clone the WhatsApp MCP repository:

```bash
cd D:\Hackathon_05\backend
git clone https://github.com/lharries/whatsapp-mcp.git
```

---

## Installation

### Step 1: Install Dependencies

```bash
cd D:\Hackathon_05\backend

# Install Python dependencies (including aiosqlite)
uv sync
```

### Step 2: Build WhatsApp Bridge

```bash
cd whatsapp-mcp/whatsapp-bridge

# Build the Go bridge
go build -o whatsapp-bridge.exe main.go

# Or run directly (for development)
go run main.go
```

**Windows Users**: You may need to install MSYS2 with ucrt64 C compiler:
```bash
# Install MSYS2 from https://www.msys2.org/
# Then in MSYS2 ucrt64 terminal:
pacman -S mingw-w64-ucrt-x86_64-gcc
```

### Step 3: Authenticate WhatsApp

```bash
cd whatsapp-mcp/whatsapp-bridge

# Run the bridge
go run main.go
```

**First Run**:
1. QR code will appear in terminal
2. Scan with WhatsApp mobile app:
   - **Android**: Settings > Linked devices > Link a device
   - **iOS**: Settings > Linked Devices > Link a Device
3. Wait for authentication to complete
4. Bridge will create SQLite databases in `store/` directory

**Note**: Authentication persists for ~20 days before re-authentication needed.

### Step 4: Configure Environment

Edit `backend/.env`:

```env
# WhatsApp MCP Configuration
WHATSAPP_MCP_BRIDGE_PATH=./whatsapp-mcp/whatsapp-bridge
WHATSAPP_MCP_ENABLED=true
WHATSAPP_POLL_INTERVAL=30
```

### Step 5: Verify Installation

```bash
# Check bridge status via API
curl http://localhost:8000/webhooks/whatsapp/status
```

Expected response:
```json
{
  "whatsapp_mcp_enabled": true,
  "bridge_path": "./whatsapp-mcp/whatsapp-bridge",
  "bridge_exists": true,
  "poll_interval": 30
}
```

---

## Usage

### Option 1: Webhook (Real-time)

Send incoming WhatsApp messages to the webhook:

```bash
curl -X POST http://localhost:8000/webhooks/whatsapp/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+923001234567",
    "message": "Hello, I need help with my account"
  }'
```

**Response**:
```json
{
  "status": "received",
  "ticket_id": "abc123-def456",
  "channel": "whatsapp"
}
```

### Option 2: Worker (Polling)

Start the WhatsApp worker to poll for new messages:

```bash
cd D:\Hackathon_05\backend
python -m src.workers.whatsapp_worker
```

**Logs**:
```
INFO: Starting WhatsApp MCP worker...
INFO: Connected to WhatsApp database: ./whatsapp-mcp/whatsapp-bridge/store/messages.db
INFO: WhatsApp MCP worker started (poll interval: 30s)
INFO: Processed 1 new WhatsApp message(s)
INFO:   - +923001234567: Hello, I need help... (ticket: abc123)
```

### Option 3: Manual Testing

Test the integration manually:

```python
# test_whatsapp_manual.py
import asyncio
from src.channels.whatsapp_mcp_client import WhatsAppMCPClient
from src.channels.whatsapp_handler import WhatsAppHandler
from src.kafka.client import FTEKafkaProducer

async def test_whatsapp():
    # Initialize client
    client = WhatsAppMCPClient(bridge_path="./whatsapp-mcp/whatsapp-bridge")
    await client.initialize()
    
    # Receive message
    msg = await client.receive_message("+923001234567")
    if msg:
        print(f"Received: {msg.message_text}")
    
    # Send message
    success = await client.send_message("+923001234567", "Hello from Customer Success FTE!")
    print(f"Message sent: {success}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(test_whatsapp())
```

---

## API Endpoints

### POST `/webhooks/whatsapp/mcp`

Receive incoming WhatsApp messages.

**Request**:
```json
{
  "phone": "+923001234567",
  "message": "Message text"
}
```

**Response**:
```json
{
  "status": "received",
  "ticket_id": "uuid-here",
  "channel": "whatsapp"
}
```

### GET `/webhooks/whatsapp/status`

Check WhatsApp MCP bridge status.

**Response**:
```json
{
  "whatsapp_mcp_enabled": true,
  "bridge_path": "./whatsapp-mcp/whatsapp-bridge",
  "bridge_exists": true,
  "poll_interval": 30
}
```

---

## Message Flow

### Incoming Message

```
1. Customer sends WhatsApp message
        ↓
2. Go bridge receives via WhatsApp Web API
        ↓
3. Message stored in SQLite (messages.db)
        ↓
4a. Webhook: API polls DB and creates ticket
        ↓
4b. Worker: Background job polls DB every 30s
        ↓
5. Kafka event published
        ↓
6. AI Agent processes message
        ↓
7. Response generated with WhatsApp formatting (≤300 chars)
```

### Outgoing Response

```
1. AI Agent generates response
        ↓
2. WhatsApp Handler truncates to 300 chars
        ↓
3. Message stored in SQLite (outgoing)
        ↓
4. Go bridge syncs with WhatsApp servers
        ↓
5. Message delivered to customer
```

---

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `WHATSAPP_MCP_BRIDGE_PATH` | `./whatsapp-mcp/whatsapp-bridge` | Path to Go bridge |
| `WHATSAPP_MCP_ENABLED` | `false` | Enable WhatsApp integration |
| `WHATSAPP_POLL_INTERVAL` | `30` | Seconds between polls |

---

## Testing

### Run Tests

```bash
cd D:\Hackathon_05\backend

# Run WhatsApp MCP tests
pytest tests/integration/test_whatsapp_mcp.py -v
```

### Test Scenarios

1. **Receive Message**: Send WhatsApp message → Verify ticket created
2. **AI Response**: Submit question → Verify response ≤300 chars
3. **Cross-Channel**: Email then WhatsApp → Verify history loaded
4. **Escalation**: Send angry message → Verify escalation triggered

---

## Troubleshooting

### Bridge Not Found

**Error**: `Go bridge executable not found`

**Solution**:
```bash
cd whatsapp-mcp/whatsapp-bridge
go build -o whatsapp-bridge.exe main.go
```

### Database Not Found

**Error**: `WhatsApp database not found at: ...`

**Solution**:
1. Run bridge to authenticate: `go run main.go`
2. Scan QR code with WhatsApp
3. Verify `store/messages.db` exists

### Authentication Expired

**Error**: `Failed to connect to WhatsApp`

**Solution**:
1. Re-authenticate: `go run main.go`
2. Scan QR code again
3. Wait for sync to complete

### Messages Not Sending

**Error**: Messages stored but not delivered

**Solution**:
1. Check Go bridge is running
2. Verify WhatsApp connection in mobile app
3. Check bridge logs for errors

---

## Production Deployment

### Docker Configuration

Add WhatsApp worker to `docker-compose.yml`:

```yaml
whatsapp:
  build: ./backend
  env_file:
    - ./backend/.env
  volumes:
    - ./backend:/app
    - ./whatsapp-mcp:/app/whatsapp-mcp
  command: python -m src.workers.whatsapp_worker
  depends_on:
    - kafka
```

### Kubernetes Deployment

Create `k8s/whatsapp-worker-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whatsapp-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: whatsapp-worker
  template:
    metadata:
      labels:
        app: whatsapp-worker
    spec:
      containers:
      - name: worker
        image: novasaas/customer-success-fte:latest
        command: ["python", "-m", "src.workers.whatsapp_worker"]
        env:
        - name: WHATSAPP_MCP_ENABLED
          value: "true"
        volumeMounts:
        - name: whatsapp-bridge
          mountPath: /app/whatsapp-mcp
      volumes:
      - name: whatsapp-bridge
        hostPath:
          path: /opt/whatsapp-mcp
```

### Monitoring

**Metrics to Track**:
- Messages received per minute
- Average response time
- Bridge connection status
- Database size
- Error rate

**Alerting**:
- Bridge disconnected > 5 minutes
- Poll failures > 10 consecutive
- Message delivery failures > 5%

---

## Security Considerations

### Data Storage

- **Messages**: Stored locally in SQLite (encrypted at rest recommended)
- **Credentials**: WhatsApp session stored in `whatsapp.db`
- **PII**: Customer phone numbers in database

### Access Control

- **API Authentication**: Required for webhook endpoints
- **Database Access**: Read-only for MCP client
- **Bridge Access**: Localhost only (no remote access)

### Compliance

- **WhatsApp ToS**: Use only for business purposes (WhatsApp Business API recommended for production)
- **GDPR**: Customer data deletion on request
- **Retention**: 2-year message retention policy

---

## Limitations

### Current Limitations

1. **Unofficial API**: Uses WhatsApp Web API (not official Business API)
2. **Single Device**: One WhatsApp number per bridge instance
3. **Local Storage**: SQLite database on local filesystem
4. **Polling**: 30-second delay for message detection
5. **Session Expiry**: Re-authentication needed every ~20 days

### Production Recommendations

For production deployment, consider:

1. **WhatsApp Business API**: Official Twilio integration (already supported)
2. **Cloud Database**: Migrate from SQLite to PostgreSQL
3. **Webhooks**: Replace polling with push notifications
4. **High Availability**: Multiple bridge instances with load balancing
5. **Monitoring**: Comprehensive logging and alerting

---

## Comparison: WhatsApp MCP vs Twilio

| Feature | WhatsApp MCP | Twilio API |
|---------|-------------|------------|
| **Cost** | Free | $0.005-0.01/message |
| **Setup** | QR code auth | Business verification |
| **Official** | ❌ Unofficial | ✅ Official |
| **Scalability** | Single number | Multi-number support |
| **Features** | Basic messaging | Templates, buttons, etc. |
| **Reliability** | Depends on bridge | 99.99% SLA |
| **Production** | ⚠️ Not recommended | ✅ Recommended |

**Recommendation**: Use WhatsApp MCP for **development/testing**, Twilio for **production**.

---

## Files Modified/Created

### Backend

| File | Status | Purpose |
|------|--------|---------|
| `pyproject.toml` | ✅ Updated | Added aiosqlite dependency |
| `.env.example` | ✅ Updated | WhatsApp MCP configuration |
| `src/config.py` | ✅ Updated | WhatsApp settings |
| `src/channels/whatsapp_handler.py` | ✅ Created | Channel handler |
| `src/channels/whatsapp_mcp_client.py` | ✅ Exists | MCP client |
| `src/workers/whatsapp_worker.py` | ✅ Created | Polling worker |
| `src/api/main.py` | ✅ Updated | Webhook endpoints |
| `src/agent/runner.py` | ✅ Updated | WhatsApp response sending |
| `src/kafka/topics.py` | ✅ Updated | WhatsApp Kafka topics |
| `tests/integration/test_whatsapp_mcp.py` | ✅ Created | Integration tests |

### Documentation

| File | Status | Purpose |
|------|--------|---------|
| `WHATSAPP_MCP_SETUP.md` | ✅ Created | This guide |

---

## Quick Start Checklist

- [ ] Clone WhatsApp MCP repository
- [ ] Install Go and Python dependencies
- [ ] Build WhatsApp bridge
- [ ] Authenticate with QR code
- [ ] Configure `.env` settings
- [ ] Start backend API
- [ ] Start WhatsApp worker
- [ ] Test webhook endpoint
- [ ] Send test message
- [ ] Verify AI response

---

## Support

**Issues**: Report via GitHub Issues  
**Documentation**: See `README.md` and this guide  
**Testing**: Run `pytest tests/integration/test_whatsapp_mcp.py`

---

**Last Updated**: 2026-02-21  
**Version**: 1.0
