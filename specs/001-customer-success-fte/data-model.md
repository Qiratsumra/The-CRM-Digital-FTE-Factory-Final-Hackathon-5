# Data Model — Customer Success FTE

**Date**: 2026-02-18
**Purpose**: Define database entities, relationships, and validation rules

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  customers  │       │   tickets   │       │ conversations │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────│ customer_id │       │ id (PK)     │
│ email       │       │ id (PK)     │◄──────│ ticket_id   │
│ phone       │       │ channel     │       │ channel     │
│ created_at  │       │ status      │       │ created_at  │
└─────────────┘       │ created_at  │       └─────────────┘
                      └─────────────┘              │
                            │                      │
                            │                      │
                            ▼                      ▼
                      ┌─────────────┐       ┌─────────────┐
                      │   messages  │       │ tool_calls  │
                      ├─────────────┤       ├─────────────┤
                      │ id (PK)     │       │ id (PK)     │
                      │ conv_id     │       │ message_id  │
                      │ direction   │       │ tool_name   │
                      │ content     │       │ arguments   │
                      │ channel     │       │ result      │
                      │ status      │       │ created_at  │
                      │ created_at  │       └─────────────┘
                      └─────────────┘
```

---

## Entities

### customers

Represents a support requester with unified identity across channels.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique customer identifier |
| email | TEXT | UNIQUE, nullable | Primary identity (from email channel or web form) |
| phone | TEXT | nullable | Secondary identity (from WhatsApp) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Customer record creation timestamp |

**Validation Rules**:
- At least one of `email` or `phone` must be present
- Email must match standard email format regex
- Phone must be E.164 format (e.g., +14155551234)

**Relationships**:
- One-to-many with `tickets`
- One-to-many with `conversations`

---

### tickets

Represents a support inquiry with lifecycle tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique ticket identifier |
| customer_id | UUID | FK → customers.id | Customer who submitted the ticket |
| channel | TEXT | NOT NULL, CHECK IN ('email', 'whatsapp', 'web_form') | Origin channel |
| status | TEXT | NOT NULL, DEFAULT 'pending', CHECK IN ('pending', 'processing', 'escalated', 'resolved', 'archived') | Current ticket status |
| subject | TEXT | nullable | Ticket subject (from email or web form) |
| priority | TEXT | DEFAULT 'normal', CHECK IN ('low', 'normal', 'high', 'urgent') | Ticket priority |
| category | TEXT | nullable | Ticket category (billing, technical, general, etc.) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ticket creation timestamp |
| last_updated | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last modification timestamp |
| escalated_at | TIMESTAMPTZ | nullable | When ticket was escalated (if applicable) |
| escalation_reason | TEXT | nullable | Reason for escalation (legal, angry_customer, etc.) |
| resolved_at | TIMESTAMPTZ | nullable | When ticket was resolved |

**Validation Rules**:
- `escalated_at` must be set when status = 'escalated'
- `resolved_at` must be set when status = 'resolved'
- `escalation_reason` required when status = 'escalated'

**Relationships**:
- Many-to-one with `customers`
- One-to-many with `conversations`
- One-to-many with `messages` (via conversations)

---

### conversations

Represents a threaded exchange within a single channel session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique conversation identifier |
| ticket_id | UUID | FK → tickets.id | Parent ticket |
| channel | TEXT | NOT NULL | Channel this conversation belongs to |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Conversation start timestamp |
| closed_at | TIMESTAMPTZ | nullable | When conversation was closed |
| idle_timeout_at | TIMESTAMPTZ | nullable | When conversation times out (24h email, 4h WhatsApp) |

**Validation Rules**:
- `idle_timeout_at` = created_at + 24h for email, + 4h for WhatsApp
- `closed_at` must be set when conversation ends

**Relationships**:
- Many-to-one with `tickets`
- One-to-many with `messages`

---

### messages

Represents individual communications (incoming or outgoing).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique message identifier |
| conversation_id | UUID | FK → conversations.id | Parent conversation |
| direction | TEXT | NOT NULL, CHECK IN ('incoming', 'outgoing') | Message direction |
| content | TEXT | NOT NULL | Message content |
| channel | TEXT | NOT NULL | Channel this message was sent/received on |
| status | TEXT | DEFAULT 'pending', CHECK IN ('pending', 'sent', 'delivered', 'failed') | Delivery status |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Message creation timestamp |
| delivered_at | TIMESTAMPTZ | nullable | When message was delivered |
| sentiment_score | NUMERIC | CHECK (0.0 <= sentiment_score <= 1.0) | Sentiment analysis result |

**Validation Rules**:
- `content` must be non-empty
- `sentiment_score` range: 0.0 (most negative) to 1.0 (most positive)
- `delivered_at` must be set when status = 'delivered'
- WhatsApp messages: content length ≤ 1600 chars (Twilio limit)

**Relationships**:
- Many-to-one with `conversations`
- One-to-many with `tool_calls`

---

### tool_calls

Represents agent tool invocations during message processing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique tool call identifier |
| message_id | UUID | FK → messages.id | Message that triggered this tool call |
| tool_name | TEXT | NOT NULL | Name of tool called (search_knowledge_base, escalate_to_human, etc.) |
| arguments | JSONB | NOT NULL | Tool call arguments |
| result | TEXT | nullable | Tool execution result |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When tool was called |

**Validation Rules**:
- `tool_name` must be one of: `search_knowledge_base`, `create_ticket`, `get_customer_history`, `send_response`, `escalate_to_human`, `analyze_sentiment`

**Relationships**:
- Many-to-one with `messages`

---

### knowledge_base_articles

Represents product documentation for semantic search.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique article identifier |
| title | TEXT | NOT NULL | Article title |
| content | TEXT | NOT NULL | Article content (Markdown) |
| category | TEXT | NOT NULL | Article category |
| tags | TEXT[] | nullable | Search tags |
| embedding | vector(768) | nullable | Gemini embedding for semantic search |
| last_updated | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |
| file_path | TEXT | UNIQUE | Git repository path |

**Validation Rules**:
- `embedding` must be 768-dimensional (Gemini embedding size)
- `file_path` must match pattern `knowledge-base/*.md`

---

### agent_metrics

Stores daily aggregated metrics for reporting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Unique metric record |
| date | DATE | NOT NULL, UNIQUE | Metric date (UTC) |
| channel | TEXT | NOT NULL | Channel this metric applies to |
| total_tickets | INTEGER | NOT NULL, DEFAULT 0 | Total tickets processed |
| avg_sentiment | NUMERIC | nullable | Average sentiment score |
| escalations | INTEGER | NOT NULL, DEFAULT 0 | Number of escalations |
| avg_response_time_sec | NUMERIC | nullable | Average response time in seconds |

**Validation Rules**:
- One record per channel per day
- `avg_sentiment` range: 0.0 to 1.0

---

## State Transitions

### Ticket Status Flow

```
pending → processing → resolved
              ↓
         escalated → resolved
              ↓
           archived (after 2 years)
```

### Message Status Flow

```
pending → sent → delivered
           ↓
         failed
```

---

## Indexes

```sql
-- Customer lookups
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);

-- Ticket queries
CREATE INDEX idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_tickets_escalated ON tickets(escalated_at) WHERE status = 'escalated';

-- Conversation queries
CREATE INDEX idx_conversations_ticket_id ON conversations(ticket_id);
CREATE INDEX idx_conversations_channel ON conversations(channel);

-- Message queries
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Knowledge base semantic search
CREATE INDEX idx_kb_embedding ON knowledge_base_articles USING ivfflat (embedding vector_cosine_ops);

-- Metrics by date
CREATE INDEX idx_metrics_date ON agent_metrics(date);
```

---

## Migration Strategy

All schema changes tracked in `database/migrations/`:

- `001_initial.sql` - Initial schema (this document's tables)
- Future migrations numbered sequentially

**Rollback Policy**: Each migration includes down script for rollback capability.
