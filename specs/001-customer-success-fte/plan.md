# Implementation Plan: Customer Success FTE

**Branch**: `001-customer-success-fte` | **Date**: 2026-02-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification for multi-channel AI customer support agent

## Summary

Build a multi-channel AI agent system that automates customer support for NovaSaaS B2B SaaS product. The system handles email (Gmail), WhatsApp (Twilio), and web form channels, processes 300+ tickets/day, searches a knowledge base for product questions, analyzes sentiment, and escalates complex cases to human agents via email notifications.

Technical approach: FastAPI backend with Kafka event intake, OpenAI Agents SDK with Gemini-2.5-flash, Neon PostgreSQL with pgvector for semantic search, and Next.js frontend for web support form.

## Technical Context

**Language/Version**: Python 3.14 (from pyproject.toml requires-python = ">=3.14")
**Primary Dependencies**: FastAPI, openai-agents SDK, google-generativeai, aiokafka, asyncpg, pydantic-settings
**Storage**: Neon PostgreSQL (serverless) with pgvector extension
**Testing**: pytest with asyncio mode
**Target Platform**: Linux server (Kubernetes deployment)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: 300+ tickets/day, P95 response time < 3s, uptime > 99.9%
**Constraints**: WhatsApp responses ≤ 300 chars, email ≤ 500 words, web ≤ 300 words; ticket ID returned within 5 seconds
**Scale/Scope**: 85 employees, 2,400 customers, 60% web form / 25% email / 15% WhatsApp channel split

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality Laws | ✅ Pass | Type hints, error handling, secrets via env, parameterized queries, JSON envelope |
| II. AI Agent Laws | ✅ Pass | Tool docstrings, Pydantic validation, send_response protocol, ticket-first, channel identity |
| III. Multi-Channel Laws | ✅ Pass | Email/phone identity, response limits, formatters.py, cross-channel history |
| IV. Database Laws | ✅ Pass | created_at with timezone, gen_random_uuid(), migrations/, pgvector |
| V. Testing Laws | ✅ Pass | Unit tests for tools/handlers, E2E for all 3 channels, transition tests, P95 < 3s |
| VI. Frontend Laws | ✅ Pass | Client+server validation, async states, Shadcn components, Tailwind classes |
| VII. Commit Message Laws | ✅ Pass | `<phase>(<scope>): <what changed>` format |

**Gate Result**: PASS - No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-customer-success-fte/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI schemas)
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .env.example
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── customer_success_agent.py   # Agent definition + Gemini config
│   │   ├── tools.py                    # All @function_tool definitions
│   │   ├── prompts.py                  # System prompts
│   │   └── formatters.py               # Channel-specific formatting
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── gmail_handler.py
│   │   ├── whatsapp_handler.py
│   │   └── web_form_handler.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── message_processor.py        # Kafka consumer + agent runner
│   │   └── metrics_collector.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app
│   │   ├── dependencies.py             # Shared dependencies (DB pool, etc.)
│   │   └── routers/
│   │       ├── webhooks.py
│   │       ├── support.py
│   │       ├── customers.py
│   │       └── metrics.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql
│   │   ├── migrations/
│   │   │   └── 001_initial.sql
│   │   ├── queries.py                  # All async DB queries
│   │   └── connection.py               # asyncpg pool setup
│   ├── kafka/
│   │   ├── __init__.py
│   │   ├── client.py                   # Producer/Consumer classes
│   │   └── topics.py                   # Topic name constants
│   ├── skills/
│   │   ├── knowledge_retrieval.py
│   │   ├── sentiment_analysis.py
│   │   ├── escalation_decision.py
│   │   ├── channel_adaptation.py
│   │   └── customer_identification.py
│   ├── mcp/
│   │   └── server.py
│   └── config.py                       # Pydantic settings
└── tests/
    ├── test_agent.py
    ├── test_channels.py
    ├── test_tools.py
    ├── test_transition.py
    └── test_e2e.py

frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx
│   │   └── support/
│   │       └── page.tsx                # Web support form
│   ├── components/
│   │   └── ui/                         # Shadcn components
│   └── services/
│       └── api.ts                      # API client
└── tests/
    └── e2e/
        └── web_form.test.ts

knowledge-base/                         # Git repository for KB articles
├── getting-started.md
├── api-reference.md
├── troubleshooting.md
└── faq.md
```

**Structure Decision**: Web application structure selected (backend + frontend + knowledge-base). Backend uses modular structure with agent/, channels/, workers/, api/, database/, kafka/, skills/, and mcp/ directories matching the architectural layers.

## Complexity Tracking

> **No constitution violations** - All principles pass without requiring justification for complexity deviations.

---

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design artifacts completed.*

| Artifact | Constitution Principles Verified | Status |
|----------|----------------------------------|--------|
| research.md | Code Quality (type hints, error handling), Database (pgvector, migrations) | ✅ |
| data-model.md | Database (created_at, gen_random_uuid(), pgvector), Multi-Channel (channel identity) | ✅ |
| api-contract.md | Code Quality (JSON envelope), Security (auth, webhook validation) | ✅ |
| quickstart.md | Testing (E2E verification), Frontend (validation, async states) | ✅ |

**Final Gate Result**: PASS - All design artifacts comply with constitution principles.
