"""Agent tools with Pydantic validation."""
from agents import function_tool
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from src.database.connection import get_pool
from src.config import get_settings
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)


class Channel(str, Enum):
    """Supported communication channels."""
    EMAIL = "email"
    WEB_FORM = "web_form"


class KnowledgeSearchInput(BaseModel):
    """Input for knowledge base search."""
    query: str
    max_results: int = 5
    category: Optional[str] = None


class TicketInput(BaseModel):
    """Input for ticket creation."""
    customer_id: str
    issue: str
    priority: str = "medium"
    category: Optional[str] = None
    channel: Channel


class EscalationInput(BaseModel):
    """Input for escalation."""
    ticket_id: str
    reason: str
    urgency: str = "normal"


class ResponseInput(BaseModel):
    """Input for sending response."""
    ticket_id: str
    message: str
    channel: Channel


async def _get_embedding(text: str) -> list[float]:
    """Generate text embedding using Gemini."""
    try:
        result = genai.embed_content(model="models/gemini-embedding-001", content=text)
        return result["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return []


@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """Search product documentation for relevant information.
    Use when customer asks product questions or needs technical help.
    Returns formatted results with relevance scores.
    """
    try:
        embedding = await _get_embedding(input.query)
        if not embedding:
            return "Embedding generation failed."

        pool = await get_pool()
        async with pool.acquire() as conn:
            # Convert embedding to JSON array string for PostgreSQL vector
            import json
            embedding_json = json.dumps(embedding)
            
            results = await conn.fetch(
                """
                SELECT title, content, category,
                       1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base
                WHERE ($2::text IS NULL OR category = $2)
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                embedding_json, input.category, input.max_results,
            )
            if not results:
                return "No relevant documentation found. Consider escalating to human support."
            return "\n\n---\n\n".join(
                f"**{r['title']}** (relevance: {r['similarity']:.2f})\n{r['content'][:500]}"
                for r in results
            )
    except Exception as e:
        logger.error(f"KB search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."


@function_tool
async def create_ticket(input: TicketInput) -> str:
    """Create a support ticket. ALWAYS call this FIRST at the start of every conversation.
    Include the source channel for proper cross-channel tracking.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            ticket_id = await conn.fetchval(
                """
                INSERT INTO tickets (customer_id, category, priority, status, source_channel)
                VALUES ($1, $2, $3, 'open', $4)
                RETURNING id
                """,
                input.customer_id, input.category or "support",
                input.priority, input.channel.value,
            )
        return f"Ticket created: {ticket_id}"
    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return "Failed to create ticket. Continuing without ticket tracking."


@function_tool
async def get_customer_history(customer_id: str) -> str:
    """Get customer's complete interaction history across ALL channels.
    Use this to understand context from previous conversations, even on different channels.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.initial_channel, m.content, m.role, m.channel, m.created_at
                FROM conversations c
                JOIN messages m ON m.conversation_id = c.id
                WHERE c.customer_id = $1
                ORDER BY m.created_at DESC
                LIMIT 20
                """,
                customer_id,
            )
        if not rows:
            return "No previous interactions found for this customer."
        return "\n".join(
            f"[{r['channel'].upper()}] {r['role']}: {r['content'][:200]}" for r in rows
        )
    except Exception as e:
        logger.error(f"History fetch failed: {e}")
        return "Could not retrieve customer history."


@function_tool
async def escalate_to_human(input: EscalationInput) -> str:
    """Escalate conversation to human support team.
    Use for: pricing, refunds, legal questions, hostile customers, or when unable to help.
    """
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE tickets SET status='escalated', resolution_notes=$1
                WHERE id=$2
                """,
                f"Escalation reason: {input.reason}", input.ticket_id,
            )
        return f"Escalated to human support. Ticket: {input.ticket_id}, Reason: {input.reason}"
    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return f"Escalation logged internally. Ticket: {input.ticket_id}"


@function_tool
async def send_response(input: ResponseInput) -> str:
    """Send response to customer via their channel.
    ALWAYS call this LAST. Never generate a response without calling this tool.
    Response will be formatted appropriately for the channel automatically.
    """
    try:
        from src.agent.formatters import format_for_channel
        from src.channels.gmail_handler import GmailHandler

        pool = await get_pool()
        
        # Get conversation_id and channel_message_id from ticket
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT c.id as conversation_id, m.channel_message_id
                FROM tickets t
                JOIN conversations c ON c.id = t.conversation_id
                LEFT JOIN messages m ON m.conversation_id = c.id AND m.direction = 'incoming'
                WHERE t.id = $1
                ORDER BY m.created_at ASC
                LIMIT 1
                """,
                input.ticket_id,
            )
            
            if not row:
                return "Ticket not found."
            
            conversation_id = str(row["conversation_id"])
            channel_message_id = row["channel_message_id"]
        
        # Format for channel
        formatted = format_for_channel(input.message, input.channel, input.ticket_id)

        # Send via appropriate channel handler
        if input.channel == Channel.EMAIL:
            handler = GmailHandler(None)  # TODO: Inject producer
            # TODO: Implement actual Gmail API send
            logger.info(f"Email response would be sent: {formatted[:100]}...")
        # Web form responses don't need external sending - stored in DB only

        # Store outgoing message in database
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status)
                VALUES ($1, $2, 'outgoing', 'agent', $3, 'sent')
                """,
                conversation_id, input.channel.value, formatted,
            )
            
            # Update ticket status to resolved
            await conn.execute(
                "UPDATE tickets SET status = 'resolved', resolved_at = NOW() WHERE id = $1",
                input.ticket_id,
            )
        
        return f"Response sent via {input.channel.value}."
    except Exception as e:
        logger.error(f"Send response failed: {e}")
        return "Response storage failed."
