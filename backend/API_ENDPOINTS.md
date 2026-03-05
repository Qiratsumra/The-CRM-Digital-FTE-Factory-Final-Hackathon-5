# API Endpoints Reference

**Base URL**: `http://localhost:8000`

**Interactive Docs**: http://localhost:8000/docs

---

## Table of Contents

1. [Health Check](#health-check)
2. [Support Tickets](#support-tickets)
3. [Webhooks](#webhooks)
4. [Customers](#customers)
5. [Metrics](#metrics)
6. [AI Agent](#ai-agent)

---

## Health Check

### GET `/health`

Check API health status and active channels.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-02-18T12:00:00Z",
  "channels": {
    "email": "active",
    "whatsapp": "active",
    "web_form": "active"
  }
}
```

---

## Support Tickets

### POST `/support/submit`

Submit a support ticket via web form.

**Request**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "How do I invite team members?",
  "category": "technical",
  "priority": "normal",
  "message": "I need help with..."
}
```

**Validation Rules**:
| Field | Constraints |
|-------|-------------|
| name | 2-100 characters |
| email | Valid email format |
| subject | 5-200 characters |
| message | 10-10000 characters |
| category | `general`, `technical`, `billing`, `bug_report`, `feedback` |
| priority | `low`, `medium`, `high`, `urgent` |

**Response** (200 OK):
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Ticket created successfully",
  "estimated_response_time": "30 seconds"
}
```

**Errors**:
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Kafka publish failure

---

### GET `/support/ticket/{ticket_id}`

Get ticket status and message history.

**Path Parameters**:
- `ticket_id`: UUID

**Response** (200 OK):
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "channel": "web_form",
  "category": "technical",
  "priority": "normal",
  "created_at": "2026-02-18T12:00:00Z",
  "last_updated": "2026-02-18T12:00:00Z"
}
```

**Errors**:
- `404 Not Found`: Ticket not found

---

## Webhooks

### POST `/webhooks/gmail`

Receive incoming email notifications from Gmail Pub/Sub.

**Headers**:
- `X-Goog-Signature`: HMAC-SHA256 signature

**Response** (200 OK):
```json
{
  "status": "processed",
  "count": 1
}
```

**Process Flow**:
1. Validate `X-Goog-Signature` header
2. Parse Pub/Sub message
3. Fetch email from Gmail API
4. Publish to Kafka topic `fte.channels.email.inbound`
5. Worker processes message and runs agent

---

### POST `/webhooks/whatsapp`

Receive incoming WhatsApp messages from Twilio.

**Headers**:
- `X-Twilio-Signature`: Twilio signature

**Form Data**:
```
From=+14155551234
Body=Hello%2C%20I%20need%20help
MessageSid=SM1234567890
```

**Response**: TwiML XML (empty)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Process Flow**:
1. Validate `X-Twilio-Signature` header
2. Parse form data
3. Normalize phone number to E.164
4. Publish to Kafka topic `fte.channels.whatsapp.inbound`
5. Worker processes message and runs agent

---

### POST `/webhooks/whatsapp/status`

Receive delivery status callbacks from Twilio.

**Form Data**:
```
MessageSid=SM1234567890
MessageStatus=delivered
```

**Response** (200 OK):
```json
{
  "status": "received"
}
```

**Status Values**:
- `sent`: Message sent
- `delivered`: Message delivered to recipient
- `failed`: Delivery failed
- `read`: Message read (if read receipts enabled)

---

## Customers

### GET `/customers/lookup`

Find customer by email or phone number.

**Query Parameters**:
- `email` (optional): Customer email address
- `phone` (optional): Customer phone in E.164 format

**Note**: At least one parameter is required.

**Example Requests**:
```bash
# Lookup by email
GET /customers/lookup?email=alice@example.com

# Lookup by phone
GET /customers/lookup?phone=+14155551234

# Both (email takes precedence)
GET /customers/lookup?email=alice@example.com&phone=+14155551234
```

**Response** (200 OK):
```json
{
  "customer_id": "cust-001",
  "email": "alice@example.com",
  "phone": "+14155551234",
  "name": "Alice Smith",
  "created_at": "2026-02-18T10:00:00Z",
  "conversations": [
    {
      "id": "conv-001",
      "channel": "email",
      "created_at": "2026-02-18T10:00:00Z",
      "message_count": 3
    }
  ],
  "channels_used": ["email", "whatsapp"]
}
```

**Errors**:
- `400 Bad Request`: Neither email nor phone provided
- `404 Not Found`: Customer not found

---

## Metrics

### GET `/metrics/channels`

Get aggregated metrics by channel.

**Query Parameters**:
- `date` (optional): Date in ISO format (defaults to today)

**Example Requests**:
```bash
# Today's metrics
GET /metrics/channels

# Specific date
GET /metrics/channels?date=2026-02-17
```

**Response** (200 OK):
```json
{
  "email": {
    "total": 75,
    "avg_sentiment": 0.65,
    "escalations": 5,
    "avg_response_time_sec": 25
  },
  "whatsapp": {
    "total": 45,
    "avg_sentiment": 0.58,
    "escalations": 8,
    "avg_response_time_sec": 18
  },
  "web_form": {
    "total": 180,
    "avg_sentiment": 0.72,
    "escalations": 12,
    "avg_response_time_sec": 22
  }
}
```

**Metrics Definitions**:
- `total`: Total tickets processed
- `avg_sentiment`: Average sentiment score (0.0-1.0)
- `escalations`: Number of escalated tickets
- `avg_response_time_sec`: Average time from message to response

---

## AI Agent

### POST `/agent/process/{ticket_id}`

Process a specific ticket with the AI agent and generate a response.

**Path Parameters**:
- `ticket_id`: UUID of the ticket to process

**Process Flow**:
1. Fetch ticket and customer from database
2. Get incoming message from conversation
3. Run AI agent with sentiment analysis
4. Search knowledge base if needed
5. Generate and store response
6. Update ticket status (resolved or escalated)

**Response** (200 OK):
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "response": "Hi John,\n\nThank you for reaching out...\n\nBest regards,\nNovaSaaS AI Support Team",
  "escalated": false
}
```

**Response Fields**:
- `ticket_id`: The processed ticket UUID
- `status`: Final ticket status (`resolved` or `escalated`)
- `response`: AI-generated response text (formatted for channel)
- `escalated`: `true` if ticket was escalated to human

**Errors**:
- `404 Not Found`: Ticket not found
- `400 Bad Request`: No incoming message found

**Example**:
```bash
curl -X POST http://localhost:8000/agent/process/550e8400-e29b-41d4-a716-446655440000
```

---

### POST `/agent/process-batch`

Process all pending tickets with the AI agent.

**Use Cases**:
- Admin dashboard manual trigger
- Scheduled cron job (e.g., every minute)
- Backlog processing

**Response** (200 OK):
```json
{
  "processed": 10,
  "resolved": 8,
  "escalated": 2,
  "failed": 0
}
```

**Response Fields**:
- `processed`: Total tickets processed
- `resolved`: Tickets resolved by AI
- `escalated`: Tickets escalated to human
- `failed`: Tickets that failed processing

**Example**:
```bash
curl -X POST http://localhost:8000/agent/process-batch
```

---

## Authentication

**Current Status**: Not implemented (development mode)

**Production Plan**:
- External endpoints (`/support/*`, `/customers/*`, `/metrics/*`) require:
  ```
  Authorization: Bearer <API_KEY>
  ```
- Webhooks validated via provider signatures:
  - Gmail: `X-Goog-Signature`
  - Twilio: `X-Twilio-Signature`

---

## Rate Limiting

**Current Status**: Not implemented

**Production Plan**:
- Web form submission: 10 requests/minute per IP
- Ticket lookup: 60 requests/minute per API key
- Metrics: 10 requests/minute per API key
- Agent processing: 30 requests/minute per API key

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1645180800
```

---

## Error Response Format

All errors follow this envelope:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid request (e.g., missing parameters)
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Invalid webhook signature
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

## Testing

Use the included test script:

```bash
# Start the API server
uvicorn src.api.main:app --reload

# Run tests (in another terminal)
python test_api.py
```

**Test Script**: `backend/test_api.py`

Tests all endpoints and validates responses.

---

## Integration Examples

### Web Form with Auto-Processing

```bash
# 1. Submit ticket
TICKET=$(curl -s -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@example.com","subject":"Help","message":"Need help"}' \
  | jq -r '.ticket_id')

# 2. Process with AI agent immediately
curl -X POST http://localhost:8000/agent/process/$TICKET
```

### Batch Processing (Cron Job)

```bash
# Add to crontab (every minute)
* * * * * curl -X POST http://localhost:8000/agent/process-batch
```
