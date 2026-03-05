# Feature Specification: Customer Success FTE

**Feature Branch**: `001-customer-success-fte`
**Created**: 2026-02-18
**Status**: Draft
**Input**: Customer Success FTE - Multi-channel AI agent for customer support automation handling email, WhatsApp, and web form channels with knowledge base search, sentiment analysis, and escalation capabilities for NovaSaaS B2B project management SaaS product

## Clarifications

### Session 2026-02-18

- Q: What authentication and authorization strategy should the system use for API endpoints? → A: API Key authentication - External clients use API keys; internal endpoints use service account tokens
- Q: When a ticket is escalated, how should the system notify and route to human agents? → A: Email notification - Send email to support team distribution list with ticket details and priority
- Q: What is the source and format of knowledge base articles the AI agent should search? → A: Markdown files in Git repository - Store in knowledge-base/ directory, sync on commit
- Q: What data retention and deletion policy should the system follow? → A: 2 years retention - Auto-archive tickets older than 2 years; manual deletion on request
- Q: What sentiment analysis approach should the system use? → A: Gemini API - Use the existing LLM to extract sentiment score as part of message processing

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Customer Submits Support Inquiry via Web Form (Priority: P1)

A customer visits the NovaSaaS support page, fills out a web form with their name, email, subject, category, priority, and message. Upon submission, they immediately receive a ticket ID and an estimated response time. The system processes their inquiry and routes it to the AI agent for response generation.

**Why this priority**: Web form is the highest volume channel (60% of 300+ daily tickets). This is the primary entry point for customer support and must work flawlessly to ensure customer satisfaction.

**Independent Test**: Can be fully tested by submitting the web form with valid data and verifying: (1) ticket ID is returned within 5 seconds, (2) ticket record exists in database, (3) customer receives confirmation with ticket ID.

**Acceptance Scenarios**:

1. **Given** a customer is on the support page with valid information, **When** they submit the web form, **Then** they receive a ticket ID and estimated response time within 5 seconds.
2. **Given** a customer submits a web form, **When** the system processes it, **Then** a ticket record is created in the database with status "pending".
3. **Given** a customer submits a product question, **When** the AI agent processes it, **Then** the agent searches the knowledge base and returns a relevant answer.

---

### User Story 2 - AI Agent Responds to Customer Product Questions (Priority: P1)

A customer sends a message via any channel (email, WhatsApp, or web form) asking a product-related question. The AI agent receives the message, searches the knowledge base for relevant information, and generates a channel-appropriate response that respects length limits and formatting requirements.

**Why this priority**: This is the core value proposition of the FTE system - automating responses to common product questions. It handles the majority of support volume and reduces human agent workload.

**Independent Test**: Can be fully tested by sending a product question via email and verifying: (1) knowledge base search is triggered, (2) response includes proper greeting and signature for email channel, (3) response accurately answers the question.

**Acceptance Scenarios**:

1. **Given** a customer asks "How do I invite team members?" via email, **When** the AI agent processes it, **Then** it searches the knowledge base and returns a response with greeting, answer, and signature.
2. **Given** a customer asks about API rate limits via WhatsApp, **When** the AI agent processes it, **Then** the response is under 300 characters and includes the rate limit information.
3. **Given** a customer submits a technical question via web form, **When** the AI agent processes it, **Then** the response is under 300 words and addresses the technical issue.

---

### User Story 3 - System Escalates Angry or Legal Requests to Human Agents (Priority: P2)

A customer sends a message containing legal keywords (e.g., "lawyer", "GDPR violation"), expresses anger (sentiment score < 0.2), or explicitly requests a human agent. The system immediately flags the ticket for escalation and either responds with an escalation message or connects directly to a human agent based on severity.

**Why this priority**: Legal inquiries and angry customers pose significant business risk if mishandled. Immediate escalation protects the company and ensures sensitive issues receive appropriate human attention.

**Independent Test**: Can be fully tested by sending a message containing "I want to speak to a lawyer" and verifying: (1) ticket status is set to "escalated", (2) escalate_to_human tool is called, (3) no AI-generated response is sent for hard escalations.

**Acceptance Scenarios**:

1. **Given** a customer email contains "GDPR violation", **When** the AI agent processes it, **Then** it immediately escalates to human without sending an AI response.
2. **Given** a WhatsApp message shows sentiment score < 0.2, **When** the AI agent processes it, **Then** it escalates and responds with "Connecting you to a human agent now".
3. **Given** a customer explicitly says "I want to speak to a manager", **When** the AI agent processes it, **Then** it escalates the ticket and notifies the support team.

---

### User Story 4 - System Maintains Customer History Across All Channels (Priority: P2)

A customer who previously emailed support with alice@corp.com later contacts via WhatsApp using their linked phone number. When the AI agent processes the new message, it loads the complete conversation history from both channels to provide context-aware responses.

**Why this priority**: Cross-channel context prevents customers from repeating themselves and enables personalized support. This is critical for customer satisfaction and efficient issue resolution.

**Independent Test**: Can be fully tested by: (1) sending an email from alice@corp.com, (2) sending a WhatsApp message from the linked phone, (3) verifying the AI agent's response references the previous email conversation.

**Acceptance Scenarios**:

1. **Given** a customer emailed yesterday about API issues, **When** they contact via WhatsApp today, **Then** the AI agent loads and references the email history in its response.
2. **Given** a customer has used all three channels over time, **When** they contact via any channel, **Then** get_customer_history returns conversations from email, WhatsApp, and web form.

---

### User Story 5 - System Tracks Response Delivery and Generates Daily Reports (Priority: P3)

After the AI agent sends responses, the system tracks delivery status via Gmail read receipts or Twilio status callbacks. At midnight UTC, the system generates a daily sentiment report showing average sentiment by channel, total tickets handled, and escalation counts for the past 24 hours.

**Why this priority**: Delivery tracking ensures messages reach customers, and daily reports provide operational visibility for support team management and continuous improvement.

**Independent Test**: Can be fully tested by: (1) sending a response and simulating a delivery confirmation webhook, (2) verifying messages.delivery_status is updated, (3) running the daily report job and verifying metrics endpoint returns correct data.

**Acceptance Scenarios**:

1. **Given** a response is sent via email, **When** Gmail sends a read receipt webhook, **Then** the messages table is updated with "delivered" status.
2. **Given** it is midnight UTC, **When** the daily report job runs, **Then** sentiment averages by channel are calculated and stored in agent_metrics table.

---

### Edge Cases

- **What happens when** a customer submits a web form with invalid or missing required fields? **Then** the system returns a 422 validation error with specific field errors.
- **How does system handle** a Kafka publish failure when creating a ticket? **Then** the system returns a 500 error and logs the failure for retry.
- **What happens when** sentiment analysis returns a score between 0.2 and 0.35 (frustrated but not hostile)? **Then** the AI agent responds but flags the ticket for human review (soft escalation).
- **How does system handle** the same issue repeated 3+ times across conversations? **Then** the ticket is flagged for human review even if sentiment is normal.
- **What happens when** a customer requests a refund or cancellation? **Then** the system immediately escalates to human (out of scope for AI agent).
- **How does system handle** a bug report with reproducible steps? **Then** the AI acknowledges and flags for engineering team review.
- **What happens when** a customer requests data deletion or export? **Then** the system escalates to human agent for manual processing (GDPR compliance).
- **How does system handle** tickets older than 2 years? **Then** they are automatically archived and excluded from active queries.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a ticket in the database before sending any response to an incoming message from any channel.
- **FR-002**: System MUST search the knowledge base when a customer asks a product-related question.
- **FR-002a**: System MUST sync knowledge base articles from the `knowledge-base/` Git repository directory and generate vector embeddings for semantic search using pgvector.
- **FR-002b**: System MUST analyze message sentiment using the Gemini API as part of message processing, returning a score between 0.0 (most negative) and 1.0 (most positive).
- **FR-003**: System MUST format responses according to channel-specific rules:
  - Email: Include greeting ("Dear" or "Hello") and signature
  - WhatsApp: Response length MUST be 300 characters or less
  - Web form: Response length MUST be 300 words or less
- **FR-004**: System MUST escalate to a human agent when any of the following are detected:
  - Sentiment score below 0.3
  - Legal keywords: "lawyer", "legal", "sue", "attorney", "GDPR violation"
  - Refund or cancellation requests
  - Explicit request for human: "human", "agent", "real person", "manager"
- **FR-004a**: System MUST send an email notification to the support team distribution list when a ticket is escalated, including ticket ID, customer email, channel, escalation reason, and full message history.
- **FR-005**: System MUST resolve customer identity by email (primary) or phone (secondary) and load conversation history from all channels before generating a response.
- **FR-006**: System MUST return a ticket ID within 5 seconds of web form submission and publish an event to the message queue.
- **FR-007**: System MUST update message delivery status when delivery confirmations are received from Gmail or Twilio.
- **FR-008**: System MUST generate a daily sentiment report at midnight UTC showing average sentiment by channel, total tickets, and escalation counts for the past 24 hours.
- **FR-009**: System MUST preserve channel identity (email, WhatsApp, web_form) in every database record.
- **FR-010**: System MUST apply channel-specific formatting in the formatter module before sending the response.

### Key Entities

- **Customer**: Represents a support requester with email (primary identifier), phone number (secondary identifier), and linked conversation history across channels.
- **Ticket**: Represents a support inquiry with a unique ID, status (pending, escalated, resolved), channel source, and associated messages.
- **Conversation**: Represents a threaded exchange between a customer and support (AI or human) within a single channel session.
- **Message**: Represents an individual communication (incoming or outgoing) with content, channel, direction, timestamp, and delivery status.
- **Knowledge Base Article**: Represents documented product information stored as Markdown files in the `knowledge-base/` Git repository directory. Each article has a title, content, category, tags, last-updated date, and vector embedding for semantic search.

## Security & Authorization

- **API Authentication**: External endpoints (web form submission, ticket lookup) require API Key authentication via `Authorization: Bearer <API_KEY>` header.
- **Webhook Validation**: Gmail webhooks validated via `X-Goog-Signature` header; Twilio webhooks validated via `X-Twilio-Signature` header.
- **Internal Endpoints**: Data endpoints (conversations, customers, metrics) use service account tokens with role-based access control.
- **Access Levels**:
  - Read-only: View tickets, conversations, metrics
  - Write: Submit tickets, update ticket status
  - Admin: Access customer data across accounts, export data

## Data Retention & Compliance

- **Retention Period**: Tickets and conversations are retained for 2 years from last activity.
- **Auto-Archival**: Tickets older than 2 years are automatically archived (moved to cold storage, excluded from active queries).
- **Manual Deletion**: Customer data deletion requests are processed manually by support team (out of scope for AI agent - escalates to human).
- **GDPR Compliance**: Customer data export requests escalate to human agent; system must support data export by customer email.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of customer product questions are answered correctly by the AI agent without human escalation.
- **SC-002**: Customers receive a ticket ID confirmation within 5 seconds of web form submission, 100% of the time.
- **SC-003**: System correctly escalates 100% of legal inquiries, angry customers (sentiment < 0.2), and explicit human requests.
- **SC-004**: Average response time for AI-handled tickets is under 30 seconds from message receipt to response delivery.
- **SC-005**: System handles 300+ tickets per day across all channels without degradation in performance or accuracy.
- **SC-006**: Customer satisfaction score for AI-handled tickets is 85% or higher (measured via post-resolution surveys).
- **SC-007**: Cross-channel customer history is correctly loaded in 95% of repeat customer interactions.
