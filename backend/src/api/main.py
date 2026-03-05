"""
Customer Success FTE API - Main Entry Point

A FastAPI application providing AI-powered customer support across:
- Email (Gmail)
- Web Form

All endpoints are defined in this single file for easy understanding.
"""
from fastapi import FastAPI, HTTPException, Header, Query, Body, Form, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from contextlib import asynccontextmanager
import uuid
import logging
import hmac
import hashlib
import base64

# Import database and Kafka
from src.database.connection import get_pool, close_pool
from src.database import queries
from src.kafka.client import FTEKafkaProducer
from src.kafka.topics import TOPICS
from src.config import get_settings
from src.agent.runner import AgentRunner

# Import rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Import Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ============================================================================
# SENTRY ERROR MONITORING
# ============================================================================

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        environment=settings.environment,
    )
    logger.info("Sentry error monitoring enabled")
else:
    logger.info("Sentry error monitoring disabled (set SENTRY_DSN to enable)")


# ============================================================================
# RATE LIMITING
# ============================================================================

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# ============================================================================
# AUTHENTICATION
# ============================================================================

async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """Verify API key for protected endpoints.
    
    In development mode, authentication is skipped.
    In production, valid API key is required.
    """
    if settings.environment == "development":
        return  # Skip auth in development
    
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def verify_twilio_signature(body: str, signature: str, url: str) -> bool:
    """Verify Twilio webhook signature."""
    if not signature:
        return False
    
    signing_key = settings.twilio_auth_token.encode()
    expected = hmac.new(
        signing_key,
        (url + body).encode(),
        hashlib.sha1
    ).digest()
    expected_b64 = base64.b64encode(expected).decode()
    return hmac.compare_digest(signature, expected_b64)


def verify_gmail_signature(payload: bytes, signature: str) -> bool:
    """Verify Gmail Pub/Sub signature."""
    # For Gmail, we validate via Pub/Sub attributes in production
    # This is a simplified version for development
    return True  # TODO: Implement proper HMAC validation with service account


# ============================================================================
# LIFESPAN MANAGEMENT - Startup and Shutdown
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs on startup and shutdown.
    """
    # STARTUP: Initialize database pool and Kafka producer
    logger.info("Starting up...")
    await get_pool()
    app.state.kafka_producer = FTEKafkaProducer()
    await app.state.kafka_producer.start()
    logger.info("Database pool and Kafka producer initialized")
    
    yield  # Application runs here
    
    # SHUTDOWN: Close connections
    logger.info("Shutting down...")
    await close_pool()
    if app.state.kafka_producer:
        await app.state.kafka_producer.stop()
    logger.info("Connections closed")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Customer Success FTE API",
    description="""
## 24/7 AI Customer Support

Automated customer support across multiple channels:
- **Email** (Gmail)
- **Web Form**

### Features
- AI-powered responses using Gemini-2.5-flash
- Cross-channel customer history
- Automatic escalation for complex issues
- Real-time sentiment analysis
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def root():
    return {"message": "Welcome to the Customer Success FTE API"}



# ============================================================================
# PYDANTIC MODELS - Request/Response Schemas
# ============================================================================

class SupportFormSubmission(BaseModel):
    """Web form submission request."""
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    subject: str = Field(..., min_length=5, max_length=200, description="Ticket subject")
    category: str = Field(default="general", description="Ticket category")
    priority: str = Field(default="medium", description="Ticket priority")
    message: str = Field(..., min_length=10, max_length=10000, description="Message content")


class TicketResponse(BaseModel):
    """Ticket creation response."""
    ticket_id: str
    message: str
    estimated_response_time: str


class TicketStatusResponse(BaseModel):
    """Ticket status response."""
    ticket_id: str
    status: str
    channel: str
    category: Optional[str] = None
    priority: Optional[str] = None
    created_at: datetime
    last_updated: datetime


class AgentProcessRequest(BaseModel):
    """Request to process a ticket with AI agent."""
    ticket_id: str


class AgentProcessResponse(BaseModel):
    """Response from AI agent processing."""
    ticket_id: str
    status: str
    response: str
    escalated: bool = False


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    channels: dict


class WebhookResponse(BaseModel):
    """Webhook processing response."""
    status: str
    count: int = 1


# ============================================================================
# ENDPOINT: Health Check
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is healthy and which channels are active"
)
async def health_check():
    """
    Health check endpoint.

    Returns current status and active channels.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "channels": {
            "email": "active",
            "web_form": "active",
        },
    }


# ============================================================================
# ENDPOINTS: Web Form Support (Customer-facing)
# ============================================================================

@app.post(
    "/support/submit",
    response_model=TicketResponse,
    tags=["Support"],
    summary="Submit Support Ticket",
    description="Submit a support ticket via web form. Returns ticket ID immediately."
)
@limiter.limit(f"{settings.rate_limit_webform_per_minute}/minute")
async def submit_support_form(request: Request, submission: SupportFormSubmission):
    """
    Submit a support ticket via web form.

    **Validation:**
    - Name: 2-100 characters
    - Email: Valid email format
    - Subject: 5-200 characters
    - Message: 10-10000 characters

    **Returns:** Ticket ID and estimated response time
    """
    pool = await get_pool()
    
    try:
        # Create or get customer
        customer_id = await queries.create_customer(
            pool, email=submission.email, name=submission.name
        )
        
        # Create ticket
        ticket_id = await queries.create_ticket(
            pool,
            customer_id=customer_id,
            source_channel="web_form",
            subject=submission.subject,
            category=submission.category,
            priority=submission.priority,
        )
        
        # Store incoming message
        # Get conversation_id from ticket
        ticket_data = await queries.get_ticket_by_id(pool, ticket_id)
        if ticket_data:
            await queries.create_message(
                pool,
                conversation_id=ticket_data["conversation_id"],
                channel="web_form",
                direction="incoming",
                role="customer",
                content=submission.message,
            )
        
        # Publish to Kafka for async processing
        producer: FTEKafkaProducer = app.state.kafka_producer
        await producer.publish(
            TOPICS["webform_inbound"],
            {
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "subject": submission.subject,
                "message": submission.message,
                "category": submission.category,
                "priority": submission.priority,
            }
        )
        
        logger.info(f"Ticket created: {ticket_id} for {submission.email}")
        
        return {
            "ticket_id": ticket_id,
            "message": "Ticket created successfully",
            "estimated_response_time": "30 seconds",
        }
        
    except Exception as e:
        logger.error(f"Ticket creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create ticket")


@app.get(
    "/support/ticket/{ticket_id}",
    response_model=TicketStatusResponse,
    tags=["Support"],
    summary="Get Ticket Status",
    description="Get ticket status and messages by ticket ID"
)
async def get_ticket_status(ticket_id: str):
    """
    Get ticket status by ID.

    Returns ticket details including status, channel, and message history.
    For WhatsApp-only tickets, returns limited info (messages not shown on web).
    """
    pool = await get_pool()

    ticket_data = await queries.get_ticket_by_id(pool, ticket_id)

    if not ticket_data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # For WhatsApp-only tickets, return limited data (messages not visible on web)
    if ticket_data.get("whatsapp_only"):
        return {
            "ticket_id": ticket_data["ticket_id"],
            "status": ticket_data["status"],
            "channel": ticket_data["channel"],
            "category": ticket_data.get("category"),
            "priority": ticket_data.get("priority"),
            "created_at": ticket_data["created_at"],
            "last_updated": ticket_data.get("resolved_at") or ticket_data["created_at"],
            "whatsapp_only": True,
        }

    return {
        "ticket_id": ticket_data["ticket_id"],
        "status": ticket_data["status"],
        "channel": ticket_data["channel"],
        "category": ticket_data.get("category"),
        "priority": ticket_data.get("priority"),
        "created_at": ticket_data["created_at"],
        "last_updated": ticket_data.get("resolved_at") or ticket_data["created_at"],
    }


# ============================================================================
# ENDPOINTS: Webhooks (Gmail)
# ============================================================================

@app.post(
    "/webhooks/gmail",
    response_model=WebhookResponse,
    tags=["Webhooks"],
    summary="Gmail Webhook",
    description="Receive incoming email notifications from Gmail Pub/Sub"
)
async def gmail_webhook(request: Request, x_goog_signature: str | None = Header(None)):
    """
    Gmail Pub/Sub webhook for incoming emails.

    **Headers:**
    - `X-Goog-Signature`: HMAC-SHA256 signature for validation

    **Process:**
    1. Validate signature
    2. Parse Pub/Sub message
    3. Fetch email from Gmail API
    4. Publish to Kafka for processing
    """
    try:
        body = await request.body()

        # Validate signature (simplified for development)
        if settings.environment != "development":
            if not verify_gmail_signature(body, x_goog_signature or ""):
                raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse Pub/Sub message
        data = await request.json()
        
        # Handle both push subscription format and direct message format
        if "message" in data:
            message = data["message"]
            attributes = message.get("attributes", {})
            history_id = attributes.get("historyId")
            
            # Also check for direct email data (for testing)
            email_data = message.get("data", "")
            if email_data:
                try:
                    decoded_data = base64.b64decode(email_data).decode("utf-8")
                    import json
                    email_payload = json.loads(decoded_data)
                    history_id = history_id or email_payload.get("historyId")
                except Exception:
                    pass
        else:
            attributes = data.get("attributes", {})
            history_id = attributes.get("historyId")

        if not history_id:
            logger.warning("No historyId in Gmail Pub/Sub message")
            # For testing, allow messages without historyId
            history_id = "0"

        # Process email via Gmail handler
        from src.channels.gmail_handler import GmailHandler
        producer: FTEKafkaProducer = app.state.kafka_producer
        gmail_handler = GmailHandler(producer)
        
        # Process the notification (will fetch emails and create tickets)
        await gmail_handler.process_notification({"message": {"attributes": {"historyId": history_id}}})

        logger.info(f"Gmail webhook processed: historyId={history_id}")

        return {"status": "processed", "count": 1}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


# ============================================================================
# ENDPOINTS: WhatsApp MCP Webhooks
# ============================================================================

@app.post(
    "/webhooks/whatsapp/mcp",
    tags=["Webhooks", "WhatsApp"],
    summary="WhatsApp MCP Webhook",
    description="Receive incoming WhatsApp messages from WhatsApp MCP"
)
async def whatsapp_mcp_webhook(
    request: Request,
):
    """
    Receive incoming WhatsApp messages via WhatsApp MCP.

    **Request Body:**
    ```json
    {
        "phone": "+923001234567",
        "message": "Hello, I need help with...",
        "timestamp": "2026-02-21T10:00:00Z"
    }
    ```

    **Process:**
    1. Validate request
    2. Create/get customer by phone
    3. Create ticket
    4. Store message
    5. Publish to Kafka for agent processing

    **Returns:** Ticket ID
    """
    try:
        from src.database import queries
        producer: FTEKafkaProducer = app.state.kafka_producer
        pool = await get_pool()

        # Parse request
        data = await request.json()
        phone = data.get("phone")
        message = data.get("message")

        if not phone or not message:
            raise HTTPException(
                status_code=400,
                detail="phone and message are required"
            )

        # Create or get customer
        async with pool.acquire() as conn:
            customer = await queries.get_customer_by_phone(conn, phone)
            if not customer:
                customer_id = await queries.create_customer(
                    conn,
                    email=None,
                    phone=phone,
                    name=f"WhatsApp User {phone[-4:]}",
                )
            else:
                customer_id = customer["id"]

            # Create ticket (creates conversation internally)
            ticket_id = await queries.create_ticket(
                conn,
                customer_id=customer_id,
                source_channel="whatsapp",
                category="support",
            )

            # Store incoming message
            # Get conversation_id from the ticket
            ticket_row = await conn.fetchrow(
                "SELECT conversation_id FROM tickets WHERE id = $1", ticket_id
            )
            if ticket_row:
                await queries.store_message(
                    conn,
                    conversation_id=ticket_row["conversation_id"],
                    channel="whatsapp",
                    direction="incoming",
                    role="customer",
                    content=message,
                )

        # Publish to Kafka for agent processing
        await producer.publish(
            TOPICS["whatsapp_inbound"],
            {
                "ticket_id": str(ticket_id),
                "customer_id": str(customer_id),
                "from": phone,
                "message": message,
                "channel": "whatsapp",
            }
        )

        logger.info(f"Processed WhatsApp message from {phone}: {message[:50]}...")

        return {
            "status": "received",
            "ticket_id": str(ticket_id),
            "channel": "whatsapp",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp MCP webhook failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@app.get(
    "/webhooks/whatsapp/status",
    tags=["Webhooks", "WhatsApp"],
    summary="WhatsApp MCP Status",
    description="Check WhatsApp MCP bridge status"
)
async def whatsapp_mcp_status():
    """
    Check WhatsApp MCP Go bridge status.

    **Returns:** Bridge status and configuration
    """
    try:
        from src.channels.whatsapp_mcp_client import WhatsAppMCPClient
        
        bridge_path = settings.whatsapp_mcp_bridge_path
        client = WhatsAppMCPClient(bridge_path=bridge_path)
        
        bridge_exists = await client.check_go_bridge_status()
        
        return {
            "whatsapp_mcp_enabled": settings.whatsapp_mcp_enabled,
            "bridge_path": bridge_path,
            "bridge_exists": bridge_exists,
            "poll_interval": settings.whatsapp_poll_interval,
        }

    except Exception as e:
        logger.error(f"Failed to check WhatsApp MCP status: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


# ============================================================================
# ENDPOINTS: Customers
# ============================================================================

@app.get(
    "/customers/lookup",
    tags=["Customers"],
    summary="Lookup Customer",
    description="Find customer by email or phone number",
    dependencies=[Depends(verify_api_key)]
)
async def lookup_customer(
    email: Optional[str] = Query(None, description="Customer email"),
    phone: Optional[str] = Query(None, description="Customer phone (E.164)")
):
    """
    Find customer by email or phone.

    **Query Parameters:**
    - `email`: Customer email (primary identifier)
    - `phone`: Customer phone in E.164 format (secondary identifier)

    **Note:** At least one parameter is required.

    **Returns:** Customer profile with conversation history across all channels.
    """
    if not email and not phone:
        raise HTTPException(
            status_code=400,
            detail="email or phone parameter is required"
        )
    
    pool = await get_pool()
    customer = await queries.get_customer_by_email_or_phone(pool, email, phone)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


# ============================================================================
# ENDPOINTS: Metrics
# ============================================================================

@app.get(
    "/metrics/channels",
    tags=["Metrics"],
    summary="Get Channel Metrics",
    description="Get aggregated metrics by channel for a specific date",
    dependencies=[Depends(verify_api_key)]
)
async def get_channel_metrics(
    date: date = Query(default_factory=date.today, description="Metrics date (UTC)")
):
    """
    Get aggregated metrics by channel.

    **Query Parameters:**
    - `date`: Date for metrics (defaults to today)

    **Returns:** Metrics for each channel including:
    - Total tickets
    - Average sentiment score
    - Number of escalations
    - Average response time
    """
    pool = await get_pool()
    metrics = await queries.get_channel_metrics(pool, datetime.fromisoformat(f"{date}T00:00:00"))
    return metrics


# ============================================================================
# ENDPOINTS: AI Agent
# ============================================================================

@app.post(
    "/agent/process/{ticket_id}",
    response_model=AgentProcessResponse,
    tags=["Agent"],
    summary="Process Ticket with AI Agent",
    description="Trigger AI agent to process a ticket and generate response",
    dependencies=[Depends(verify_api_key)]
)
async def process_ticket_with_agent(ticket_id: str):
    """
    Process a ticket with the AI agent.

    **Path Parameters:**
    - `ticket_id`: UUID of the ticket to process

    **Process:**
    1. Fetch ticket and customer from database
    2. Get incoming message from conversation
    3. Run AI agent with sentiment analysis
    4. Search knowledge base if needed
    5. Generate and store response
    6. Update ticket status (resolved or escalated)

    **Returns:** Agent response and ticket status
    """
    pool = await get_pool()
    
    # Get ticket details
    ticket = await queries.get_ticket_by_id(pool, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get customer message from conversation
    async with pool.acquire() as conn:
        message_row = await conn.fetchrow(
            """
            SELECT m.content, m.id as message_id
            FROM messages m
            WHERE m.conversation_id = $1
            AND m.direction = 'incoming'
            ORDER BY m.created_at ASC
            LIMIT 1
            """,
            ticket["conversation_id"],
        )
        
        if not message_row:
            raise HTTPException(status_code=400, detail="No incoming message found")
        
        customer_message = message_row["content"]
    
    # Get customer ID
    async with pool.acquire() as conn:
        customer_row = await conn.fetchrow(
            "SELECT customer_id FROM tickets WHERE id = $1", ticket_id
        )
        customer_id = str(customer_row["customer_id"])
    
    # Run AI agent
    runner = AgentRunner()
    response = await runner.process_message(
        ticket_id=ticket_id,
        customer_id=customer_id,
        message=customer_message,
        channel=ticket["channel"],
    )
    
    # Get updated ticket status
    updated_ticket = await queries.get_ticket_by_id(pool, ticket_id)
    
    # Check if escalated
    escalated = updated_ticket["status"] == "escalated" if updated_ticket else False
    
    return {
        "ticket_id": ticket_id,
        "status": updated_ticket["status"] if updated_ticket else "unknown",
        "response": response,
        "escalated": escalated,
    }


@app.post(
    "/agent/process-batch",
    tags=["Agent"],
    summary="Process All Pending Tickets",
    description="Trigger AI agent to process all pending tickets",
    dependencies=[Depends(verify_api_key)]
)
async def process_all_pending_tickets():
    """
    Process all pending tickets with the AI agent.

    **Returns:** Summary of processed tickets
    """
    pool = await get_pool()
    
    # Get all pending tickets
    async with pool.acquire() as conn:
        tickets = await conn.fetch(
            """
            SELECT t.id, t.customer_id, t.source_channel as channel, m.content as message
            FROM tickets t
            JOIN conversations c ON c.id = t.conversation_id
            JOIN messages m ON m.conversation_id = c.id
            WHERE t.status = 'open'
            AND m.direction = 'incoming'
            ORDER BY t.created_at ASC
            """
        )
    
    results = {
        "processed": 0,
        "resolved": 0,
        "escalated": 0,
        "failed": 0,
    }
    
    runner = AgentRunner()
    
    for ticket in tickets:
        try:
            ticket_id = str(ticket["id"])
            customer_id = str(ticket["customer_id"])
            message = ticket["message"]
            channel = ticket["channel"]
            
            response = await runner.process_message(
                ticket_id=ticket_id,
                customer_id=customer_id,
                message=message,
                channel=channel,
            )
            
            results["processed"] += 1
            
            # Check final status
            updated = await queries.get_ticket_by_id(pool, ticket_id)
            if updated:
                if updated["status"] == "escalated":
                    results["escalated"] += 1
                elif updated["status"] == "resolved":
                    results["resolved"] += 1
                    
        except Exception as e:
            logger.error(f"Failed to process ticket {ticket['id']}: {e}")
            results["failed"] += 1
    
    return results


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
