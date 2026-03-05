# API Contract — Customer Success FTE

**Date**: 2026-02-18
**Base URL**: `https://support-api.novasaas.com`
**Version**: 1.0.0

---

## Authentication

All non-webhook endpoints require:
```
Authorization: Bearer <API_KEY>
```

Webhook endpoints validated by:
- Gmail: `X-Goog-Signature` header
- Twilio: `X-Twilio-Signature` header

---

## Endpoints

### Health Check

#### GET /health

**Purpose**: System health verification

**Response**: `200 OK`
```json
{
  "data": {
    "status": "healthy",
    "channels": ["email", "whatsapp", "web_form"],
    "timestamp": "2026-02-18T12:00:00Z"
  },
  "error": null,
  "metadata": {
    "version": "1.0.0"
  }
}
```

---

### Web Form Support

#### POST /support/submit

**Purpose**: Submit a support ticket via web form

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "How do I invite team members?",
  "category": "technical",
  "priority": "normal",
  "message": "I just signed up and need to add my colleagues..."
}
```

**Validation Rules**:
- `email`: valid email format (required)
- `name`: 1-100 characters (required)
- `message`: 10-10000 characters (required)
- `category`: one of `technical`, `billing`, `general`, `feature_request`
- `priority`: one of `low`, `normal`, `high`, `urgent`

**Response**: `200 OK`
```json
{
  "data": {
    "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Ticket created successfully",
    "estimated_response_time": "30 seconds"
  },
  "error": null,
  "metadata": {
    "channel": "web_form",
    "created_at": "2026-02-18T12:00:00Z"
  }
}
```

**Errors**:
- `422 Unprocessable Entity`: Validation failure
  ```json
  {
    "data": null,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input",
      "details": [
        {"field": "email", "message": "Invalid email format"},
        {"field": "message", "message": "Message must be at least 10 characters"}
      ]
    },
    "metadata": {}
  }
  ```
- `500 Internal Server Error`: Kafka publish failure

---

#### GET /support/ticket/{ticket_id}

**Purpose**: Retrieve ticket status and messages

**Path Parameters**:
- `ticket_id`: UUID

**Response**: `200 OK`
```json
{
  "data": {
    "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "resolved",
    "channel": "web_form",
    "subject": "How do I invite team members?",
    "messages": [
      {
        "id": "msg-001",
        "direction": "incoming",
        "content": "How do I invite team members?",
        "created_at": "2026-02-18T12:00:00Z",
        "status": "delivered"
      },
      {
        "id": "msg-002",
        "direction": "outgoing",
        "content": "To invite team members, go to Settings > Team...",
        "created_at": "2026-02-18T12:00:15Z",
        "status": "delivered"
      }
    ],
    "created_at": "2026-02-18T12:00:00Z",
    "last_updated": "2026-02-18T12:00:15Z"
  },
  "error": null,
  "metadata": {
    "message_count": 2
  }
}
```

**Errors**:
- `404 Not Found`: Ticket not found

---

### Webhooks

#### POST /webhooks/gmail

**Purpose**: Receive incoming emails from Gmail

**Headers**:
- `X-Goog-Signature`: HMAC-SHA256 signature for validation

**Request Body** (Pub/Sub push message):
```json
{
  "message": {
    "data": "base64_encoded_email_data",
    "attributes": {
      "historyId": "123456"
    }
  }
}
```

**Response**: `200 OK`
```json
{
  "status": "processed",
  "count": 1
}
```

**Errors**:
- `403 Forbidden`: Invalid signature

---

#### POST /webhooks/whatsapp

**Purpose**: Receive WhatsApp messages from Twilio

**Headers**:
- `X-Twilio-Signature`: Twilio signature for validation

**Request Body** (form-encoded):
```
MessageSid=SM1234567890
From=+14155551234
Body=Hello, I need help with...
```

**Response**: TwiML XML (empty response)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Errors**:
- `403 Forbidden`: Invalid signature

---

#### POST /webhooks/whatsapp/status

**Purpose**: Receive delivery status callbacks from Twilio

**Request Body** (form-encoded):
```
MessageSid=SM1234567890
MessageStatus=delivered
```

**Response**: `200 OK`
```json
{
  "status": "received"
}
```

---

### Data Endpoints

#### GET /conversations/{conversation_id}

**Purpose**: Retrieve full conversation with customer and channel history

**Path Parameters**:
- `conversation_id`: UUID

**Response**: `200 OK`
```json
{
  "data": {
    "conversation_id": "conv-001",
    "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
    "channel": "email",
    "customer": {
      "id": "cust-001",
      "email": "alice@corp.com",
      "phone": "+14155551234"
    },
    "messages": [
      {
        "id": "msg-001",
        "direction": "incoming",
        "content": "Question about API limits",
        "channel": "email",
        "created_at": "2026-02-18T10:00:00Z",
        "sentiment_score": 0.5
      }
    ],
    "channel_history": [
      {
        "channel": "email",
        "last_contact": "2026-02-17T08:00:00Z",
        "ticket_count": 3
      },
      {
        "channel": "whatsapp",
        "last_contact": "2026-02-16T14:00:00Z",
        "ticket_count": 1
      }
    ]
  },
  "error": null,
  "metadata": {
    "total_messages": 5
  }
}
```

**Errors**:
- `404 Not Found`: Conversation not found

---

#### GET /customers/lookup

**Purpose**: Find customer by email or phone, return unified profile

**Query Parameters**:
- `email`: optional, email address
- `phone`: optional, E.164 phone number

**Note**: At least one parameter required

**Response**: `200 OK`
```json
{
  "data": {
    "customer_id": "cust-001",
    "email": "alice@corp.com",
    "phone": "+14155551234",
    "conversations": [
      {
        "id": "conv-001",
        "channel": "email",
        "created_at": "2026-02-18T10:00:00Z",
        "message_count": 3
      }
    ],
    "channels_used": ["email", "whatsapp"]
  },
  "error": null,
  "metadata": {
    "total_conversations": 4
  }
}
```

**Errors**:
- `400 Bad Request`: Neither email nor phone provided
- `404 Not Found`: Customer not found

---

#### GET /metrics/channels

**Purpose**: Get aggregated metrics by channel

**Query Parameters**:
- `date`: optional, ISO date (defaults to today)

**Response**: `200 OK`
```json
{
  "data": {
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
  },
  "error": null,
  "metadata": {
    "date": "2026-02-18",
    "total_tickets": 300,
    "total_escalations": 25
  }
}
```

---

## Error Response Format

All errors follow this envelope:
```json
{
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  },
  "metadata": {}
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Invalid webhook signature |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

- **Web form submission**: 10 requests per minute per IP
- **Ticket lookup**: 60 requests per minute per API key
- **Metrics endpoints**: 10 requests per minute per API key

Rate limit headers included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1645180800
```
