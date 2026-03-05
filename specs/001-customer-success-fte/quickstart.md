# Quickstart — Customer Success FTE

**Date**: 2026-02-18
**Purpose**: Get the system running locally for development

---

## Prerequisites

- Python 3.14 (managed via `uv`)
- Node.js 18+ (for frontend)
- Docker + Docker Compose
- Git

---

## Local Development Setup

### 1. Clone and Navigate

```bash
cd D:\Hackathon_05
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your credentials:
# - GEMINI_API_KEY=your_gemini_key
# - NEON_DATABASE_URL=postgresql://...
# - KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env:
# - NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Start Infrastructure (Kafka + Zookeeper)

```bash
cd D:\Hackathon_05

docker compose up -d kafka zookeeper
```

### 5. Run Database Migrations

```bash
cd backend

# Apply migrations
uv run python -m src.database.migrations.apply
```

### 6. Sync Knowledge Base

```bash
# Copy KB articles to repository
cp ../knowledge-base/*.md ../knowledge-base/

# Generate embeddings
uv run python -m src.skills.knowledge_retrieval --sync
```

---

## Run the System

### Option A: Docker Compose (All Services)

```bash
docker compose up -d
```

Services:
- `api` on http://localhost:8000
- `worker` (background consumer)
- `frontend` on http://localhost:3000
- `kafka` on localhost:9092
- `zookeeper` on localhost:2181

### Option B: Manual (Development Mode)

**Terminal 1 - API:**
```bash
cd backend
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Worker:**
```bash
cd backend
uv run python -m src.workers.message_processor
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## Verify Setup

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"data": {"status": "healthy", "channels": ["email", "whatsapp", "web_form"], "timestamp": "..."}}
```

### 2. Submit Test Ticket

```bash
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Test Ticket",
    "category": "general",
    "priority": "normal",
    "message": "This is a test message to verify the system works."
  }'
```

Expected:
```json
{"data": {"ticket_id": "...", "message": "Ticket created successfully", "estimated_response_time": "30 seconds"}}
```

### 3. Check Ticket Status

```bash
curl http://localhost:8000/support/ticket/<ticket_id> \
  -H "Authorization: Bearer test-api-key"
```

### 4. Frontend Form

Open http://localhost:3000/support and submit a test message.

---

## Run Tests

```bash
cd backend

# Unit tests
uv run pytest tests/test_tools.py -v

# Channel tests
uv run pytest tests/test_channels.py -v

# E2E tests (requires running services)
uv run pytest tests/test_e2e.py -v
```

---

## Common Tasks

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f worker
```

### Reset Database

```bash
cd backend
uv run python -m src.database.migrations.reset
uv run python -m src.database.migrations.apply
```

### Clear Kafka Topics

```bash
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic fte.tickets.incoming
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic fte.tickets.incoming --partitions 3 --replication-factor 1
```

---

## Troubleshooting

### Worker Not Processing Messages

1. Check Kafka connection:
   ```bash
   docker compose ps
   ```

2. Verify topic exists:
   ```bash
   docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

3. Check worker logs:
   ```bash
   docker compose logs worker
   ```

### Database Connection Errors

1. Verify Neon URL in `.env`
2. Test connection:
   ```bash
   uv run python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('your-url'))"
   ```

### Frontend API Calls Failing

1. Verify `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env`
2. Check API is running: `curl http://localhost:8000/health`

---

## Next Steps

- Read `data-model.md` for database schema details
- Read `api-contract.md` for endpoint specifications
- Read `research.md` for technology decisions and rationale
- Run `/sp.tasks` to generate implementation task list
