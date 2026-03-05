# Customer Success FTE API

A FastAPI-based API for AI-powered customer support across Email, WhatsApp, and Web Form channels.

## Quick Start

```bash
# Install dependencies
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your credentials

# Run the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

All endpoints are defined in `src/api/main.py` for easy understanding.

### Health Check

```bash
GET /health
```

Returns API health status and active channels.

### Support Tickets

```bash
# Submit a support ticket via web form
POST /support/submit
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "How do I invite team members?",
  "category": "technical",
  "priority": "normal",
  "message": "I need help with..."
}

# Get ticket status
GET /support/ticket/{ticket_id}
```

### Webhooks

```bash
# Gmail incoming email webhook
POST /webhooks/gmail
Headers: X-Goog-Signature: <signature>

# WhatsApp incoming message webhook
POST /webhooks/whatsapp
Headers: X-Twilio-Signature: <signature>
Content-Type: application/x-www-form-urlencoded

From=+14155551234&Body=Hello&MessageSid=SM123

# WhatsApp delivery status webhook
POST /webhooks/whatsapp/status
```

### Customers

```bash
# Lookup customer by email or phone
GET /customers/lookup?email=alice@example.com
GET /customers/lookup?phone=+14155551234
```

### Metrics

```bash
# Get channel metrics for a specific date
GET /metrics/channels?date=2026-02-18
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── src/
│   ├── api/
│   │   └── main.py              # All API endpoints (single file)
│   ├── agent/
│   │   ├── customer_success_agent.py
│   │   ├── tools.py              # Agent tools with @function_tool
│   │   ├── prompts.py            # System prompts
│   │   └── formatters.py         # Channel formatting
│   ├── channels/
│   │   ├── gmail_handler.py      # Gmail API handler
│   │   └── whatsapp_handler.py   # Twilio/WhatsApp handler
│   ├── database/
│   │   ├── schema.sql            # Database schema
│   │   ├── connection.py         # asyncpg pool
│   │   └── migrations/
│   │       └── 001_initial.sql   # Initial migration
│   ├── kafka/
│   │   ├── topics.py             # Topic constants
│   │   └── client.py             # Producer/Consumer
│   ├── skills/
│   │   ├── knowledge_retrieval.py
│   │   ├── sentiment_analysis.py
│   │   ├── escalation_decision.py
│   │   ├── channel_adaptation.py
│   │   └── customer_identification.py
│   ├── workers/
│   │   └── message_processor.py  # Kafka consumer + agent runner
│   └── config.py                 # Pydantic settings
├── tests/
│   ├── conftest.py
│   ├── test_transition.py
│   ├── test_tools.py
│   ├── test_channels.py
│   └── test_e2e.py
├── .env.example
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Configuration

Edit `.env` with your credentials:

```env
# Gemini API
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash

# Neon PostgreSQL
DATABASE_URL=postgresql://user:pass@host/db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Twilio
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx

# App
API_KEY=dev-api-key
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest --cov=src tests/
```

## Docker

```bash
# Build and run with Docker Compose
docker compose up -d

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

## License

MIT
"# CRM-Digital-FTE-Factory-Final-Hackathon-5-backend" 
