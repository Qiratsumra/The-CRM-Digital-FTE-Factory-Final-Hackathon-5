# Customer Success FTE

AI-powered multi-channel customer support automation for NovaSaaS.

## Overview

This system provides 24/7 automated customer support across:
- **Email** (Gmail)
- **Web Form** (Next.js)

Powered by Google's Gemini 2.5-flash AI with automatic escalation to human agents.

**Key Feature**: AI responses are automatically sent to customer's email!

## Quick Start

### Prerequisites

- Python 3.14+
- Node.js 18+
- Docker & Docker Compose (optional)
- UV package manager (`pip install uv`)

### 1. Clone and Setup

```bash
cd Hackathon_05
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
# - GEMINI_API_KEY: Get from Google AI Studio
# - DATABASE_URL: Neon PostgreSQL connection string
# - GMAIL_SENDER_EMAIL: Your Gmail address
# - GMAIL_SENDER_PASSWORD: Gmail app password

# See GMAIL_SETUP.md for Gmail configuration

# Run database migrations
python -m src.database.run_migrations

# Sync knowledge base
python -m src.skills.knowledge_sync ../knowledge-base

# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start the development server
npm run dev
```

### 4. Run with Docker Compose (Alternative)

```bash
# From project root
docker compose up -d
```

Services:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000

### 5. Run Without Docker (Development)

**Backend:**
```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Worker:**
```bash
cd backend
python -m src.workers.message_processor
```

**Metrics Collector:**
```bash
cd backend
python -m src.workers.metrics_collector --scheduled
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage

### 1. Submit a Support Ticket

1. Go to **http://localhost:3000/support**
2. Fill out the form (name, email, subject, message)
3. Click "Submit Support Ticket"
4. Copy the ticket ID from the confirmation

### 2. Get AI Response

1. Go to **http://localhost:3000/process**
2. Paste your ticket ID
3. Click "Lookup"
4. Click "Generate AI Response"
5. View the AI-generated answer

**Or** after submitting a ticket, click the "Get AI Response" button on the confirmation page.

### 3. Check Ticket Status

Visit **http://localhost:3000/process** and enter your ticket ID to see the current status.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/support/submit` | POST | Submit support ticket |
| `/support/ticket/{id}` | GET | Get ticket status |
| `/customers/lookup` | GET | Lookup customer |
| `/metrics/channels` | GET | Channel metrics |
| `/agent/process/{id}` | POST | Process ticket with AI |
| `/webhooks/gmail` | POST | Gmail webhook |

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/contract/test_web_form.py -v

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Frontend Tests

```bash
cd frontend

# Run linting
npm run lint
```

## Project Structure

```
Hackathon_05/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI endpoints
│   │   ├── agent/         # AI agent & tools
│   │   ├── channels/      # Email handlers
│   │   ├── database/      # DB schema & queries
│   │   ├── kafka/         # Kafka client & topics
│   │   ├── skills/        # AI skills (sentiment, escalation)
│   │   └── workers/       # Kafka message processors
│   ├── tests/
│   │   ├── contract/      # API contract tests
│   │   ├── integration/   # End-to-end tests
│   │   └── unit/          # Unit tests
│   └── knowledge-base/    # Product documentation
├── frontend/
│   ├── app/               # Next.js pages
│   ├── components/        # React components
│   └── lib/               # Utilities
├── specs/                 # Feature specifications
└── docker-compose.yml     # Docker services
```

## Configuration

### Backend (.env)

```env
# Gemini API
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# App
API_KEY=dev-api-key
ENVIRONMENT=development
```

### Frontend (.env)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

### AI Agent Capabilities

- **Sentiment Analysis**: Scores 0.0-1.0 using Gemini API
- **Knowledge Base Search**: Semantic search with pgvector embeddings
- **Automatic Escalation**: For legal, refund, angry customers
- **Channel Formatting**: Email (greeting+signature), Web (≤300 words)
- **Cross-Channel History**: Unified customer view across all channels

### Success Criteria

- ✅ 90% of questions answered by AI without escalation
- ✅ Ticket ID returned within 5 seconds
- ✅ 100% escalation rate for legal/angry customers
- ✅ <30 second average response time
- ✅ Handle 300+ tickets/day

## Knowledge Base

Sync product documentation:

```bash
cd backend
python -m src.skills.knowledge_sync ../knowledge-base
```

Articles are stored in `knowledge-base/` directory as Markdown files.

## Monitoring

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f metrics
```

### Metrics

Get channel metrics:

```bash
curl http://localhost:8000/metrics/channels?date=2026-02-18
```

Daily reports are generated at midnight UTC.

## Deployment

### Docker

```bash
# Build images
docker compose build

# Deploy
docker compose up -d

# Stop
docker compose down
```

### Kubernetes (Production)

See `k8s/` directory for deployment manifests.

## Troubleshooting

### Database Connection Failed

```bash
# Check DATABASE_URL in .env
# Verify Neon PostgreSQL is accessible
# Run migrations
python -m src.database.run_migrations
```

### Kafka Connection Failed

```bash
# Start Kafka with Docker Compose
docker compose up kafka zookeeper

# Or update KAFKA_BOOTSTRAP_SERVERS
```

### AI Agent Not Responding

```bash
# Check GEMINI_API_KEY is valid
# Verify knowledge base is synced
python -m src.skills.knowledge_sync
# Check worker logs
docker compose logs -f worker
```

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and write tests
3. Run tests: `pytest`
4. Commit: `git commit -m "feat(scope): description"`
5. Push and create PR

## License

MIT

## Support

Submit issues via GitHub or contact support@novasaas.com.
"# The-CRM-Digital-FTE-Factory-Final-Hackathon-5" 
