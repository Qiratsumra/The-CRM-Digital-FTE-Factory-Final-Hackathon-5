# Quick Reference Card - Customer Success FTE

**Last Updated:** 2026-02-23
**Status:** Production Ready

---

## 🚀 Quick Start (First Time)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
# - GEMINI_API_KEY: Get from https://aistudio.google.com/app/apikey
# - DATABASE_URL: Neon PostgreSQL connection string
# - GMAIL_SENDER_EMAIL: Your Gmail address
# - GMAIL_SENDER_PASSWORD: Gmail app password

# Run database migrations
uv run python -m src.database.run_migrations

# Start API server
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

### 3. Access Application

- **Frontend:** http://localhost:3000
- **Admin Dashboard:** http://localhost:3000/admin
- **API Docs:** http://localhost:8000/docs

---

## 📧 Email Receiving Options

### Option A: IMAP Polling (Recommended for Dev/Demo)

**No Google Workspace required!**

```bash
# 1. Enable IMAP in Gmail
# https://myaccount.google.com/lesssecureapps

# 2. Generate app password
# https://myaccount.google.com/apppasswords

# 3. Add to .env
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_SENDER_PASSWORD=your-app-password
IMAP_POLL_INTERVAL=60

# 4. Run poller
uv run python -m src.channels.imap_poller --interval 60
```

**Docs:** `backend/IMAP_POLLING_SETUP.md`

---

### Option B: Gmail API (Production)

**Requires Google Workspace domain delegation**

```bash
# 1. Enable Gmail API in Google Cloud Console
# 2. Grant domain-wide delegation
# 3. Share inbox with service account
# 4. Run webhook receiver

uv run uvicorn src.api.main:app --reload
# Webhook: POST /webhooks/gmail
```

**Docs:** `backend/GMAIL_API_SETUP.md`

---

## 🧪 Testing Commands

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=src

# Run specific test file
uv run pytest tests/unit/test_tools.py -v
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test metrics (requires API key in production)
curl -H "X-API-Key: dev-api-key" http://localhost:8000/metrics/channels

# Submit support ticket
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "How do I invite team members?",
    "message": "I need help with inviting team members to my workspace."
  }'
```

---

## 🔧 Configuration Reference

### Backend .env

```env
# Gemini API
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

# Database
DATABASE_URL=postgresql://user:pass@host/db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Gmail
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_SENDER_PASSWORD=your-app-password
GMAIL_API_ENABLED=true

# IMAP Polling
IMAP_POLL_INTERVAL=60

# App
ENVIRONMENT=development
API_KEY=dev-api-key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_WEBFORM_PER_MINUTE=10

# Sentry (Optional)
SENTRY_DSN=
```

### Frontend .env

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📡 API Endpoints

### Public (No Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/support/submit` | POST | Submit support ticket |
| `/support/ticket/{id}` | GET | Get ticket status |
| `/webhooks/gmail` | POST | Gmail webhook |

### Protected (Requires API Key)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/customers/lookup` | GET | Find customer by email/phone |
| `/metrics/channels` | GET | Channel metrics |
| `/agent/process/{id}` | POST | Process ticket with AI |
| `/agent/process-batch` | POST | Process all pending tickets |

**Usage:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/metrics/channels
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Customer Success FTE                    │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   Frontend   │     │    Backend   │     │   Database   │ │
│  │   Next.js    │────▶│   FastAPI    │────▶│  PostgreSQL  │ │
│  │  :3000       │     │   :8000      │     │   +pgvector  │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│                            │                                 │
│                            ▼                                 │
│                     ┌──────────────┐                        │
│                     │  Kafka       │                        │
│                     │  Message     │                        │
│                     │  Queue       │                        │
│                     └──────────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Gmail      │  │  WhatsApp    │  │  Web Form    │      │
│  │  (IMAP/API)  │  │   (MCP)      │  │  (Next.js)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Admin Dashboard

**URL:** http://localhost:3000/admin

**Features:**
- Total tickets, resolutions, escalations
- Average response time
- Per-channel metrics (Email, WhatsApp, Web Form)
- Sentiment analysis (color-coded)
- Escalation rate with progress bars
- Date selector for historical data

**Usage:**
1. Open dashboard
2. Select date
3. Enter API key (dev-api-key for development)
4. Click "Refresh"

---

## 🔐 Security

### API Key Authentication

**Development:**
```env
ENVIRONMENT=development  # Auth disabled
API_KEY=dev-api-key
```

**Production:**
```env
ENVIRONMENT=production  # Auth enabled
API_KEY=your-secure-random-key
```

**Usage:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/metrics/channels
```

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/support/submit` | 10/minute |
| All others | 60/minute |

### Sentry Error Monitoring

```env
SENTRY_DSN=https://your-dsn@sentry.io/0
```

---

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check DATABASE_URL in .env
# Verify Neon PostgreSQL is accessible
# Run migrations
uv run python -m src.database.run_migrations
```

### Kafka Connection Failed

```bash
# Start Kafka with Docker Compose
docker compose up kafka zookeeper

# Or update KAFKA_BOOTSTRAP_SERVERS
```

### Gmail IMAP Polling Failed

```bash
# 1. Enable IMAP in Gmail settings
# 2. Generate app password (not regular password)
# 3. Check logs for errors
uv run python -m src.channels.imap_poller --once
```

### API Key Authentication Failed

```bash
# In development, auth is disabled
# Set ENVIRONMENT=development in .env

# In production, include API key
curl -H "X-API-Key: your-api-key" http://localhost:8000/metrics/channels
```

---

## 📁 Project Structure

```
Hackathon_05/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── agent/            # AI agent & tools
│   │   ├── channels/         # Email, WhatsApp handlers
│   │   ├── database/         # PostgreSQL queries
│   │   ├── kafka/            # Kafka client & topics
│   │   ├── skills/           # AI skills (sentiment, KB)
│   │   └── workers/          # Background processors
│   ├── tests/                # Test suite
│   └── .env                  # Configuration
├── frontend/
│   ├── app/                  # Next.js pages
│   │   ├── admin/            # Admin dashboard
│   │   ├── process/          # Track ticket
│   │   └── support/          # Support forms
│   └── .env                  # Configuration
├── .github/workflows/        # CI/CD pipeline
├── specs/                    # Feature specifications
└── knowledge-base/           # Product documentation
```

---

## 🎯 Demo Script

### 1. Start Services

```bash
# Terminal 1 - Backend
cd backend
uv run uvicorn src.api.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - IMAP Poller (optional)
cd backend
uv run python -m src.channels.imap_poller --interval 60
```

### 2. Demo Flow

1. **Home Page** (http://localhost:3000)
   - Show channel selection
   - Explain multi-channel support

2. **Submit Ticket** (http://localhost:3000/support/webform)
   - Fill out form
   - Show ticket ID response

3. **Admin Dashboard** (http://localhost:3000/admin)
   - Show metrics
   - Explain rate limiting, authentication

4. **API Documentation** (http://localhost:8000/docs)
   - Show Swagger UI
   - Demonstrate endpoints

5. **Code Walkthrough**
   - Show CI/CD pipeline
   - Explain architecture

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Set `ENVIRONMENT=production`
- [ ] Generate secure `API_KEY`
- [ ] Configure `SENTRY_DSN` (optional)
- [ ] Update `DATABASE_URL` for production
- [ ] Set up Kafka cluster
- [ ] Configure SSL/TLS

### GitHub Secrets

- [ ] `DATABASE_URL`
- [ ] `GEMINI_API_KEY`
- [ ] `GMAIL_SENDER_EMAIL`
- [ ] `GMAIL_SENDER_PASSWORD`

### Deploy

```bash
# Docker Compose
docker compose up -d

# Or Kubernetes (manifests not included)
kubectl apply -f k8s/
```

---

## 🔗 Important Links

- **Frontend:** http://localhost:3000
- **Admin Dashboard:** http://localhost:3000/admin
- **API Docs:** http://localhost:8000/docs
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📚 Documentation

- `README.md` - Main project documentation
- `COMPLETION_REPORT.md` - Feature completion status
- `backend/IMAP_POLLING_SETUP.md` - IMAP polling setup
- `backend/GMAIL_API_SETUP.md` - Gmail API setup
- `backend/API_ENDPOINTS.md` - API reference
- `specs/001-customer-success-fte/spec.md` - Feature specification

---

**Quick Start Command:**
```bash
# From project root
docker compose up -d
```

**Support:** Submit issues via GitHub or contact support@novasaas.com
