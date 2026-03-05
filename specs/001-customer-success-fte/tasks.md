# Tasks: Customer Success FTE

**Input**: Design documents from `/specs/001-customer-success-fte/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are INCLUDED in this task list following TDD approach. Write tests FIRST, ensure they FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Paths follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create backend directory structure per plan.md in `backend/src/{agent,channels,workers,api,database,kafka,skills,mcp}/` with `__init__.py` stubs
- [ ] T002 [P] Create frontend directory structure per plan.md in `frontend/src/{app,components,services}/` with Shadcn UI setup
- [ ] T003 [P] Create `knowledge-base/` directory with initial Markdown articles (`getting-started.md`, `api-reference.md`, `troubleshooting.md`, `faq.md`)
- [ ] T004 [P] Configure backend dependencies in `backend/pyproject.toml` (FastAPI, openai-agents, google-generativeai, aiokafka, asyncpg, pydantic-settings)
- [ ] T005 [P] Configure frontend dependencies in `frontend/package.json` (Next.js 14, Shadcn UI, Tailwind CSS)
- [X] T006 [P] Create `backend/.env.example` with all required environment variables (GEMINI_API_KEY, NEON_DATABASE_URL, KAFKA_BOOTSTRAP_SERVERS, etc.)
- [ ] T007 [P] Create `frontend/.env.example` with `NEXT_PUBLIC_API_URL`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 [P] Implement `backend/src/config.py` with pydantic-settings for all environment variables
- [X] T009 [P] Create `backend/database/schema.sql` with all 7 tables (customers, tickets, conversations, messages, tool_calls, knowledge_base_articles, agent_metrics)
- [X] T010 [P] Enable pgvector extension in `backend/database/schema.sql`
- [X] T011 [P] Create `backend/database/migrations/001_initial.sql` with full schema
- [X] T012 [P] Implement `backend/database/connection.py` with asyncpg connection pool setup
- [ ] T013 [P] Implement `backend/database/queries.py` with typed async functions for all entities
- [X] T014 [P] Create `backend/kafka/topics.py` with topic name constants (fte.tickets.incoming, fte.metrics)
- [X] T015 [P] Implement `backend/kafka/client.py` with FTEKafkaProducer and FTEKafkaConsumer classes
- [X] T016 [P] Implement `backend/src/agent/formatters.py` with `format_for_channel()` function for email, WhatsApp, web_form
- [X] T017 [P] Create `backend/src/api/main.py` with all endpoints in a single file for easy understanding
- [X] T018 [P] Implement `backend/src/api/main.py` with FastAPI app, CORS middleware, and all routes
- [X] T019 [X] ~~Create `backend/src/api/routers/webhooks.py`~~ (consolidated into main.py)
- [X] T020 [X] ~~Create `backend/src/api/routers/support.py`~~ (consolidated into main.py)
- [X] T021 [X] ~~Create `backend/src/api/routers/customers.py`~~ (consolidated into main.py)
- [X] T022 [X] ~~Create `backend/src/api/routers/metrics.py`~~ (consolidated into main.py)
- [X] T023 [P] Implement `backend/src/api/main.py` with GET `/health` endpoint returning status, channels, timestamp
- [X] T024 [P] Create `backend/tests/conftest.py` with pytest fixtures (asyncio mode, test DB setup)
- [X] T025 [P] Create `docker-compose.yml` with api, worker, kafka, zookeeper, frontend services
- [X] T026 [P] Create `backend/Dockerfile` for Python 3.14 with uv
- [ ] T027 [P] Create `frontend/Dockerfile` for Node.js 18

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Customer Submits Support Inquiry via Web Form (Priority: P1) 🎯 MVP

**Goal**: Customer can submit support ticket via web form and receive ticket ID within 5 seconds

**Independent Test**: Submit web form with valid data and verify: (1) ticket ID returned within 5 seconds, (2) ticket record exists in database, (3) customer receives confirmation

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T028 [P] [US1] Create contract test for POST /support/submit in `backend/tests/contract/test_web_form.py::test_submit_returns_ticket_id`
- [ ] T029 [P] [US1] Create integration test for web form submission in `backend/tests/integration/test_web_form_e2e.py::test_full_submission_flow`
- [ ] T030 [P] [US1] Create frontend E2E test in `frontend/tests/e2e/web_form.test.ts::test_form_submission_creates_ticket`

### Implementation for User Story 1

- [ ] T031 [P] [US1] Create Customer model in `backend/database/queries.py` with create_customer(email, phone) function
- [ ] T032 [P] [US1] Create Ticket model in `backend/database/queries.py` with create_ticket(customer_id, channel, subject, category, priority) function
- [ ] T033 [P] [US1] Create Conversation model in `backend/database/queries.py` with create_conversation(ticket_id, channel) function
- [ ] T034 [P] [US1] Create Message model in `backend/database/queries.py` with create_message(conversation_id, direction, content, channel) function
- [ ] T035 [US1] Implement `backend/src/channels/web_form_handler.py` with SupportFormSubmission Pydantic model and validators
- [ ] T036 [US1] Implement POST `/support/submit` endpoint in `backend/src/api/routers/support.py` with validation
- [ ] T037 [US1] Implement Kafka event publishing in `backend/src/channels/web_form_handler.py` to fte.tickets.incoming topic
- [ ] T038 [US1] Implement GET `/support/ticket/{ticket_id}` endpoint in `backend/src/api/routers/support.py`
- [ ] T039 [P] [US1] Create `frontend/src/components/SupportForm.tsx` with all form fields (name, email, subject, category, priority, message)
- [ ] T040 [P] [US1] Create `frontend/src/components/TicketStatus.tsx` for displaying ticket ID and status
- [ ] T041 [US1] Create `frontend/src/app/support/page.tsx` with form integration and success state
- [ ] T042 [US1] Add client-side validation in `frontend/src/components/SupportForm.tsx` (email format, required fields, message length)
- [ ] T043 [US1] Add loading/error/success states in `frontend/src/app/support/page.tsx`
- [X] T044 [US1] Implement `backend/src/workers/message_processor.py` with UnifiedMessageProcessor class skeleton
- [X] T045 [US1] Implement `resolve_customer()` function in `backend/src/workers/message_processor.py` (email or phone lookup/create)
- [ ] T046 [US1] Implement `get_or_create_conversation()` function in `backend/src/workers/message_processor.py`
- [X] T047 [US1] Add structured error handling in `backend/src/workers/message_processor.py` with graceful fallback
- [X] T048 [US1] Add logging for web form operations in `backend/src/workers/message_processor.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently
- Customer can submit web form at `/support`
- Ticket is created in database
- Ticket ID returned within 5 seconds
- Event published to Kafka for processing

---

## Phase 4: User Story 2 - AI Agent Responds to Customer Product Questions (Priority: P1)

**Goal**: AI agent processes customer questions, searches knowledge base, and returns channel-appropriate responses

**Independent Test**: Send product question via email and verify: (1) knowledge base search triggered, (2) response includes greeting and signature for email, (3) response accurately answers question

### Tests for User Story 2 ⚠️

- [ ] T049 [P] [US2] Create contract test for knowledge base search in `backend/tests/contract/test_knowledge_base.py::test_search_returns_relevant_results`
- [ ] T050 [P] [US2] Create integration test for email response in `backend/tests/integration/test_email_response.py::test_email_includes_greeting_and_signature`
- [ ] T051 [P] [US2] Create test for WhatsApp response length in `backend/tests/integration/test_channel_formatting.py::test_whatsapp_response_under_300_chars`

### Implementation for User Story 2

- [X] T052 [P] [US2] Implement `backend/src/skills/knowledge_retrieval.py` with search_knowledge_base(query) using pgvector similarity search
- [X] T053 [P] [US2] Implement `backend/src/skills/sentiment_analysis.py` with analyze_sentiment(text) using Gemini API
- [X] T054 [P] [US2] Implement `backend/src/skills/escalation_decision.py` with should_escalate(sentiment, keywords) function
- [X] T055 [P] [US2] Implement `backend/src/skills/channel_adaptation.py` with get_channel_constraints(channel) function
- [X] T056 [US2] Implement `backend/src/agent/tools.py` with @function_tool decorated search_knowledge_base tool
- [X] T057 [US2] Implement `backend/src/agent/tools.py` with @function_tool decorated send_response tool
- [X] T058 [US2] Implement `backend/src/agent/tools.py` with @function_tool decorated create_ticket tool
- [X] T059 [US2] Implement `backend/src/agent/tools.py` with @function_tool decorated get_customer_history tool
- [X] T060 [US2] Implement `backend/src/agent/tools.py` with @function_tool decorated escalate_to_human tool
- [X] T061 [US2] Add Pydantic input models for each tool in `backend/src/agent/tools.py`
- [X] T062 [US2] Add try/except with structured logging in every tool function
- [X] T063 [US2] Implement `backend/src/agent/prompts.py` with full system prompt for customer success agent
- [X] T064 [US2] Implement `backend/src/agent/customer_success_agent.py` with Agent() definition using Gemini-2.5-flash config
- [ ] T065 [US2] Implement `process_message()` function in `backend/src/workers/message_processor.py` with full agent run loop
- [ ] T066 [US2] Integrate channel formatter in `backend/src/workers/message_processor.py` before send_response call
- [X] T067 [US2] Implement `backend/src/channels/gmail_handler.py` with GmailHandler class (get_message, send_reply methods)
- [X] T068 [US2] Implement `backend/src/channels/whatsapp_handler.py` with WhatsAppHandler class (process_webhook, send_message, format_response methods)
- [X] T069 [US2] Implement webhook validation in `backend/src/channels/whatsapp_handler.py` with Twilio signature check
- [X] T070 [US2] Implement `backend/src/api/routers/webhooks.py` POST `/webhooks/gmail` endpoint with X-Goog-Signature validation
- [X] T071 [US2] Implement `backend/src/api/routers/webhooks.py` POST `/webhooks/whatsapp` endpoint with X-Twilio-Signature validation
- [ ] T072 [US2] Add logging for agent tool calls in `backend/src/agent/tools.py`

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently
- AI agent can process messages from all 3 channels
- Knowledge base search returns relevant results
- Responses are channel-formatted (email greeting/signature, WhatsApp ≤300 chars, web ≤300 words)

---

## Phase 5: User Story 3 - System Escalates Angry or Legal Requests to Human Agents (Priority: P2)

**Goal**: System detects escalation triggers and routes to human agents with proper notification

**Independent Test**: Send message with "I want to speak to a lawyer" and verify: (1) ticket status set to "escalated", (2) escalate_to_human tool called, (3) no AI response sent for hard escalations

### Tests for User Story 3 ⚠️

- [ ] T073 [P] [US3] Create test for legal keyword escalation in `backend/tests/integration/test_escalation.py::test_legal_keyword_triggers_escalation`
- [ ] T074 [P] [US3] Create test for angry customer escalation in `backend/tests/integration/test_escalation.py::test_low_sentiment_triggers_escalation`
- [ ] T075 [P] [US3] Create test for human request escalation in `backend/tests/integration/test_escalation.py::test_explicit_human_request_escalation`

### Implementation for User Story 3

- [ ] T076 [P] [US3] Implement escalation rules in `backend/src/skills/escalation_decision.py` with HARD_ESCALATION_KEYWORDS list
- [ ] T077 [P] [US3] Implement soft escalation detection in `backend/src/skills/escalation_decision.py` (sentiment 0.2-0.35, repeated issues)
- [ ] T078 [US3] Implement escalate_to_human tool in `backend/src/agent/tools.py` with ticket status update to "escalated"
- [ ] T079 [US3] Implement escalation email notification in `backend/src/agent/tools.py` (send to support distribution list)
- [ ] T080 [US3] Add escalation_reason field population in `backend/database/queries.py` update_ticket_status function
- [ ] T081 [US3] Implement escalation response templates in `backend/src/agent/formatters.py` (email, WhatsApp, web form variants)
- [ ] T082 [US3] Add escalation flagging logic in `backend/src/workers/message_processor.py` process_message function
- [ ] T083 [US3] Implement soft escalation flag (no AI response block, just flag for human review)
- [ ] T084 [US3] Add logging for escalation events in `backend/src/agent/tools.py`

**Checkpoint**: At this point, User Stories 1-3 should all work independently
- Legal inquiries escalate immediately
- Angry customers (sentiment < 0.2) escalate
- Explicit human requests escalate
- Support team receives email notification with ticket details

---

## Phase 6: User Story 4 - System Maintains Customer History Across All Channels (Priority: P2)

**Goal**: Customer history loaded from all channels before agent responds

**Independent Test**: Send email from alice@corp.com, then WhatsApp from linked phone, verify AI response references previous email conversation

### Tests for User Story 4 ⚠️

- [ ] T085 [P] [US4] Create test for cross-channel history in `backend/tests/integration/test_cross_channel.py::test_loads_email_history_for_whatsapp`
- [ ] T086 [P] [US4] Create test for customer identity resolution in `backend/tests/integration/test_customer_identity.py::test_link_by_email_and_phone`

### Implementation for User Story 4

- [ ] T087 [P] [US4] Implement `backend/src/skills/customer_identification.py` with resolve_customer(email, phone) function
- [ ] T088 [US4] Implement get_customer_history tool in `backend/src/agent/tools.py` with cross-channel query
- [ ] T089 [US4] Implement `backend/database/queries.py` get_customer_conversations(customer_id, channels) function
- [ ] T090 [US4] Add customer history loading in `backend/src/workers/message_processor.py` before agent run
- [ ] T091 [US4] Implement account linking logic in `backend/src/skills/customer_identification.py` (detect email in WhatsApp message)
- [ ] T092 [US4] Add conversation idle timeout logic (24h email, 4h WhatsApp) in `backend/src/workers/message_processor.py`
- [ ] T093 [US4] Implement GET `/customers/lookup` endpoint in `backend/src/api/routers/customers.py` with email/phone query params
- [ ] T094 [US4] Implement GET `/conversations/{conversation_id}` endpoint in `backend/src/api/routers/support.py` with channel_history
- [ ] T095 [US4] Add logging for customer history loading in `backend/src/workers/message_processor.py`

**Checkpoint**: At this point, User Stories 1-4 should all work independently
- Customer identified by email (primary) or phone (secondary)
- Full conversation history loaded from all channels
- AI response references previous interactions

---

## Phase 7: User Story 5 - System Tracks Response Delivery and Generates Daily Reports (Priority: P3)

**Goal**: Delivery status tracked via webhooks; daily sentiment report generated at midnight UTC

**Independent Test**: Send response, simulate delivery webhook, verify messages.delivery_status updated; run daily report job, verify metrics endpoint returns correct data

### Tests for User Story 5 ⚠️

- [ ] T096 [P] [US5] Create test for delivery status update in `backend/tests/integration/test_delivery_tracking.py::test_webhook_updates_delivery_status`
- [ ] T097 [P] [US5] Create test for daily report generation in `backend/tests/integration/test_metrics.py::test_daily_report_calculates_sentiment`

### Implementation for User Story 5

- [ ] T098 [P] [US5] Implement `backend/src/api/routers/webhooks.py` POST `/webhooks/whatsapp/status` endpoint for Twilio status callbacks
- [ ] T099 [US5] Implement delivery status update in `backend/database/queries.py` update_message_status function
- [ ] T100 [US5] Implement Gmail read receipt webhook handler in `backend/src/channels/gmail_handler.py`
- [ ] T101 [P] [US5] Create `backend/src/workers/metrics_collector.py` with daily report job (runs at midnight UTC)
- [ ] T102 [US5] Implement sentiment aggregation in `backend/src/workers/metrics_collector.py` (avg by channel, escalation counts)
- [ ] T103 [US5] Implement agent_metrics table insert in `backend/database/queries.py`
- [ ] T104 [US5] Implement GET `/metrics/channels` endpoint in `backend/src/api/routers/metrics.py` with date query param
- [ ] T105 [US5] Add delivery status field to Message model in `backend/database/queries.py`
- [ ] T106 [US5] Add logging for delivery tracking in `backend/src/channels/gmail_handler.py` and `backend/src/channels/whatsapp_handler.py`

**Checkpoint**: All user stories should now be independently functional
- Delivery status tracked via Gmail/Twilio webhooks
- Daily sentiment report generated at midnight UTC
- Metrics endpoint returns channel statistics

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T107 [P] Create `backend/tests/test_e2e.py` with full multi-channel E2E suite (TestWebFormChannel, TestEmailChannel, TestWhatsAppChannel, TestCrossChannelContinuity, TestChannelMetrics)
- [X] T108 [P] Create `backend/tests/test_transition.py` with 6 transition tests (empty message, pricing escalation, angry customer, channel response lengths, tool execution order)
- [X] T109 [P] Create `backend/tests/test_tools.py` with unit tests for all 5 agent tools
- [X] T110 [P] Create `backend/tests/test_channels.py` with unit tests for channel handlers
- [ ] T111 [P] Create `k8s/namespace.yaml` for Kubernetes deployment
- [ ] T112 [P] Create `k8s/configmap.yaml` with non-secret configuration
- [ ] T113 [P] Create `k8s/secrets.yaml` template for API keys
- [ ] T114 [P] Create `k8s/deployment-api.yaml` with 3 replicas and health probes
- [ ] T115 [P] Create `k8s/deployment-worker.yaml` with 3 replicas
- [ ] T116 [P] Create `k8s/service.yaml` for API exposure
- [ ] T117 [P] Create `k8s/ingress.yaml` with TLS configuration
- [ ] T118 [P] Create `k8s/hpa.yaml` with HPA for API and Worker
- [ ] T119 [P] Write `README.md` in repository root with project overview and quickstart link
- [ ] T120 [P] Run load test baseline verification (P95 < 3s, 300+ tickets/day capacity)
- [ ] T121 [P] Security hardening review (API key rotation, webhook signature validation, SQL injection prevention)
- [ ] T122 [P] Documentation updates in `knowledge-base/` with all product docs
- [ ] T123 [P] Sync knowledge base embeddings via `backend/src/skills/knowledge_retrieval.py --sync`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 (sentiment analysis, escalation tools)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 (customer history tool)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Minimal dependencies, can run in parallel

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for POST /support/submit in backend/tests/contract/test_web_form.py"
Task: "Integration test for web form submission in backend/tests/integration/test_web_form_e2e.py"
Task: "Frontend E2E test in frontend/tests/e2e/web_form.test.ts"

# Launch all models for User Story 1 together:
Task: "Create Customer model in backend/database/queries.py"
Task: "Create Ticket model in backend/database/queries.py"
Task: "Create Conversation model in backend/database/queries.py"
Task: "Create Message model in backend/database/queries.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Submit web form at `/support`
   - Verify ticket ID returned within 5 seconds
   - Verify ticket exists in database
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (core AI value)
4. Add User Story 3 → Test independently → Deploy/Demo (risk mitigation)
5. Add User Story 4 → Test independently → Deploy/Demo (cross-channel UX)
6. Add User Story 5 → Test independently → Deploy/Demo (operational visibility)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (web form + basic processing)
   - Developer B: User Story 2 (AI agent + channel handlers)
   - Developer C: User Story 3 (escalation logic)
3. After US1-3 complete:
   - Developer A: User Story 4 (cross-channel history)
   - Developer B: User Story 5 (delivery tracking + metrics)
   - Developer C: Phase 8 Polish (K8s, E2E tests, docs)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
