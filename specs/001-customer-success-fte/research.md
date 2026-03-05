# Research — Customer Success FTE

**Date**: 2026-02-18
**Purpose**: Document technical decisions, alternatives considered, and best practices for implementation

---

## Decision: Use Gemini-2.5-flash Instead of GPT-4o

**Category**: AI/LLM Provider

### Decision
Use Gemini-2.5-flash via `google-generativeai` SDK, wrapped in OpenAI Agents SDK via the OpenAI-compatible endpoint.

### Rationale
- **Cost**: ~$0.075/1M input tokens vs $2.50/1M for GPT-4o (33x cheaper)
- **Speed**: Gemini-2.5-flash optimized for low-latency responses
- **Context Window**: 1M tokens sufficient for full conversation history
- **Compatibility**: OpenAI Agents SDK supports custom `base_url` + `api_key`
- **Tool Support**: Compatible with `@function_tool` decorator pattern

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| GPT-4o | Better tool call reliability, mature ecosystem | 33x more expensive | Cost prohibitive for hackathon + production |
| Claude 3.5 Sonnet | Strong reasoning, good tool use | No OpenAI SDK compatibility | Would require rewriting agent framework |
| Local LLM (Llama 3) | No API costs, full control | Infrastructure complexity, slower | Overkill for hackathon timeline |

### Implementation
```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Customer Success FTE",
    model="gemini-2.5-flash",
    model_settings=ModelSettings(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=settings.gemini_api_key
    ),
)
```

### Consequences
- Must test `tool_calls` parsing (Gemini format differs slightly from OpenAI)
- Need fallback handling for Gemini-specific response formats
- Cost savings enable higher volume processing

---

## Decision: Use Neon Serverless PostgreSQL

**Category**: Database

### Decision
Use Neon's serverless PostgreSQL with `asyncpg` connection pool.

### Rationale
- **Pre-initialized**: Already set up in project — no additional configuration
- **Auto-scaling**: Compute scales automatically; cold starts ~300ms acceptable for async workers
- **pgvector**: Built-in extension critical for knowledge base semantic search
- **Free Tier**: 0.5 GB storage sufficient for hackathon volume
- **Async-Native**: `asyncpg` provides excellent async performance

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Supabase | Real-time subscriptions, generous free tier | pgvector requires manual setup | Neon simpler for vector search use case |
| AWS RDS | Full control, predictable pricing | Overprovisioning for hackathon | Unnecessary operational complexity |
| PlanetScale | MySQL-compatible, serverless | No pgvector support | Vector search is mandatory requirement |

### Implementation
```python
from config import settings
import asyncpg

DATABASE_URL = settings.neon_database_url
pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
```

### Consequences
- Cold start latency on first query after idle period (~300ms)
- Connection pooling via `asyncpg` sufficient; PgBouncer not needed
- Must handle connection refresh for long-running workers

---

## Decision: Use Apache Kafka for Event Intake

**Category**: Message Queue / Event Streaming

### Decision
Use Apache Kafka via `aiokafka` for decoupling ticket intake from processing.

### Rationale
- **Decoupling**: Separates webhook reception from agent processing
- **Buffer Spikes**: Handles traffic bursts without overwhelming workers
- **Replayability**: Events persisted for debugging and reprocessing
- **Scalability**: Multiple workers can consume from same topic
- **Hackathon Stack**: Already in project dependencies

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Redis Streams | Simpler setup, lower latency | No replay beyond retention window | Kafka more robust for event sourcing |
| RabbitMQ | Mature, easier operational model | Less suitable for event streaming | Kafka better fit for event-driven architecture |
| AWS SQS | Managed, no ops | No fan-out, limited streaming | Kafka enables future analytics use cases |

### Implementation
```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

# Producer (webhook handler)
producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
await producer.send_and_wait("fte.tickets.incoming", key=ticket_id, value=message_json)

# Consumer (worker)
consumer = AIOKafkaConsumer("fte.tickets.incoming", group_id="worker-group")
async for msg in consumer:
    await process_ticket(msg.key, msg.value)
```

### Consequences
- Need to manage Kafka cluster (docker-compose for local, K8s for prod)
- Must handle consumer lag monitoring
- Event schema evolution needs consideration

---

## Best Practice: OpenAI Agents SDK for Agent Framework

**Category**: Agent Framework

### Pattern
Use OpenAI Agents SDK with `@function_tool` decorators for all agent capabilities.

### Why This Pattern
- **Declarative**: Tools defined as Python functions with type hints
- **Automatic Schema**: SDK generates tool definitions for LLM
- **Validation**: Pydantic models for tool inputs
- **Error Handling**: Built-in retry and fallback mechanisms
- **Constitution Compliance**: Matches "AI Agent Laws" principle

### Implementation Pattern
```python
from agents import function_tool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str
    channel: str

@function_tool
async def search_knowledge_base(input: SearchInput) -> str:
    """Search the knowledge base for product documentation.
    Call when customer asks product questions.
    """
    # Implementation here
```

---

## Best Practice: Channel-Aware Response Formatting

**Category**: Multi-Channel Architecture

### Pattern
Separate channel formatting logic in `formatters.py` applied BEFORE `send_response`.

### Why This Pattern
- **Single Responsibility**: Formatting isolated from agent logic
- **Testability**: Channel formatters independently testable
- **Constitution Compliance**: Matches "Multi-Channel Laws" principle
- **Extensibility**: New channels add formatter without agent changes

### Implementation Pattern
```python
# formatters.py
def format_for_channel(channel: str, content: str) -> str:
    if channel == "email":
        return f"Dear Customer,\n\n{content}\n\nBest regards,\nNovaSaaS Support"
    elif channel == "whatsapp":
        return content[:300]  # Hard limit
    elif channel == "web_form":
        return truncate_to_words(content, 300)
```

---

## Best Practice: Database Migration Strategy

**Category**: Database Operations

### Pattern
Track all schema changes in `database/migrations/` with sequential SQL files.

### Why This Pattern
- **Audit Trail**: Full history of schema evolution
- **Reproducibility**: Fresh environments apply migrations in order
- **Rollback**: Each migration includes down script
- **Constitution Compliance**: Matches "Database Laws" principle

### Implementation Pattern
```sql
-- migrations/001_initial.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Integration Pattern: Webhook Security

**Category**: Security

### Pattern
Validate webhook signatures using provider-specific verification.

### Why This Pattern
- **Authenticity**: Ensures webhooks from legitimate Gmail/Twilio sources
- **Security**: Prevents spoofed webhook injection
- **Standard Practice**: Industry-standard for webhook handling

### Implementation Pattern
```python
# Gmail (X-Goog-Signature)
import hmac
import hashlib

def verify_gmail_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(settings.gmail_webhook_secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

# Twilio (X-Twilio-Signature)
from twilio.request_validator import RequestValidator

validator = RequestValidator(settings.twilio_auth_token)
is_valid = validator.validate(url, params, signature)
```

---

## Summary of Technology Choices

| Component | Technology | Rationale |
|-----------|------------|-----------|
| LLM | Gemini-2.5-flash | Cost-effective, fast, large context |
| Agent Framework | OpenAI Agents SDK | Declarative tools, Pydantic validation |
| Database | Neon PostgreSQL | Serverless, pgvector, auto-scaling |
| Message Queue | Apache Kafka + aiokafka | Event decoupling, replayability |
| Web Framework | FastAPI | Async-native, OpenAPI docs |
| Frontend | Next.js 14 + Shadcn | App Router, component library |
| Deployment | Kubernetes | Orchestration, HPA for workers |
