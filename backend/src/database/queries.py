"""Database queries for Customer Success FTE."""
from asyncpg import Pool
from typing import Optional
from datetime import datetime, timedelta
import uuid
import secrets


async def get_customer_by_phone(conn, phone: str) -> Optional[dict]:
    """Get customer by phone number."""
    row = await conn.fetchrow(
        "SELECT id, email, phone, name FROM customers WHERE phone = $1", phone
    )
    if row:
        return dict(row)
    return None


async def create_customer(
    conn,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
) -> str:
    """Create or get existing customer by email/phone. Returns customer ID."""
    if email:
        existing = await conn.fetchrow(
            "SELECT id FROM customers WHERE email = $1", email
        )
        if existing:
            return str(existing["id"])

    if phone:
        existing = await conn.fetchrow(
            "SELECT id FROM customers WHERE phone = $1", phone
        )
        if existing:
            if email:
                await conn.execute(
                    "UPDATE customers SET email = $1 WHERE id = $2", email, existing["id"]
                )
            return str(existing["id"])

    customer_id = await conn.fetchval(
        """
        INSERT INTO customers (email, phone, name)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        email, phone, name,
    )
    return str(customer_id)


async def create_conversation(conn, customer_id: str, channel: str) -> str:
    """Create a conversation. Returns conversation ID."""
    conversation_id = await conn.fetchval(
        """
        INSERT INTO conversations (customer_id, initial_channel, status)
        VALUES ($1, $2, 'active')
        RETURNING id
        """,
        customer_id, channel,
    )
    return str(conversation_id)


async def store_message(
    conn,
    conversation_id: str,
    channel: str,
    direction: str,
    role: str,
    content: str,
) -> str:
    """Store a message. Returns message ID."""
    message_id = await conn.fetchval(
        """
        INSERT INTO messages (conversation_id, channel, direction, role, content)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        conversation_id, channel, direction, role, content,
    )
    return str(message_id)


async def create_ticket(
    conn,
    customer_id: str,
    source_channel: str,
    subject: Optional[str] = None,
    category: Optional[str] = None,
    priority: str = "medium",
) -> str:
    """Create a support ticket. Returns ticket ID."""
    conversation_id = await conn.fetchval(
        """
        INSERT INTO conversations (customer_id, initial_channel, status)
        VALUES ($1, $2, 'active')
        RETURNING id
        """,
        customer_id, source_channel,
    )

    verification_token = generate_verification_token()
    token_expires_at = datetime.utcnow() + timedelta(hours=24)
    whatsapp_only = source_channel == "whatsapp"

    ticket_id = await conn.fetchval(
        """
        INSERT INTO tickets (conversation_id, customer_id, source_channel, category, priority, status, verification_token, token_expires_at, whatsapp_only)
        VALUES ($1, $2, $3, $4, $5, 'open', $6, $7, $8)
        RETURNING id
        """,
        conversation_id, customer_id, source_channel, category, priority, verification_token, token_expires_at, whatsapp_only,
    )

    return str(ticket_id)


def generate_verification_token() -> str:
    """Generate a unique verification token (6-character alphanumeric code)."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(chars) for _ in range(6))


async def create_message(
    conn,
    conversation_id: str,
    channel: str,
    direction: str,
    role: str,
    content: str,
) -> str:
    """Create a message record. Returns message ID."""
    message_id = await conn.fetchval(
        """
        INSERT INTO messages (conversation_id, channel, direction, role, content)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        conversation_id, channel, direction, role, content,
    )
    return str(message_id)


async def get_ticket(conn, ticket_id: str) -> Optional[dict]:
    """Get ticket by ID. Alias for get_ticket_by_id."""
    return await get_ticket_by_id(conn, ticket_id)


async def get_ticket_by_id(conn, ticket_id: str) -> Optional[dict]:
    """Get ticket by ID with customer and conversation info."""
    row = await conn.fetchrow(
        """
        SELECT
            t.id, t.status, t.source_channel as channel, t.category, t.priority,
            t.created_at, t.resolved_at, t.resolution_notes, t.whatsapp_only,
            c.id as conversation_id,
            cust.email, cust.phone, cust.name,
            m.content as first_message
        FROM tickets t
        JOIN conversations c ON c.id = t.conversation_id
        JOIN customers cust ON cust.id = t.customer_id
        LEFT JOIN messages m ON m.conversation_id = c.id AND m.direction = 'incoming'
        WHERE t.id = $1
        ORDER BY m.created_at ASC
        LIMIT 1
        """,
        ticket_id,
    )
    if not row:
        return None

    return {
        "ticket_id": str(row["id"]),
        "conversation_id": str(row["conversation_id"]),
        "customer_id": str(row["email"]),
        "status": row["status"],
        "channel": row["channel"],
        "category": row["category"],
        "priority": row["priority"],
        "created_at": row["created_at"].isoformat(),
        "resolved_at": row["resolved_at"].isoformat() if row["resolved_at"] else None,
        "whatsapp_only": row["whatsapp_only"],
    }


async def get_ticket_by_verification_token(conn, token: str) -> Optional[dict]:
    """Get ticket by verification token."""
    row = await conn.fetchrow(
        """
        SELECT
            t.id, t.status, t.source_channel as channel, t.category, t.priority,
            t.created_at, t.resolved_at, t.resolution_notes,
            c.id as conversation_id,
            cust.email, cust.phone, cust.name,
            m.content as first_message
        FROM tickets t
        JOIN conversations c ON c.id = t.conversation_id
        JOIN customers cust ON cust.id = t.customer_id
        LEFT JOIN messages m ON m.conversation_id = c.id AND m.direction = 'incoming'
        WHERE t.verification_token = $1
        AND (t.token_expires_at IS NULL OR t.token_expires_at > NOW())
        ORDER BY m.created_at ASC
        LIMIT 1
        """,
        token,
    )
    if not row:
        return None

    return {
        "ticket_id": str(row["id"]),
        "conversation_id": str(row["conversation_id"]),
        "customer_id": str(row["email"]),
        "customer_email": row["email"],
        "customer_name": row["name"],
        "status": row["status"],
        "channel": row["channel"],
        "category": row["category"],
        "priority": row["priority"],
        "created_at": row["created_at"].isoformat(),
        "resolved_at": row["resolved_at"].isoformat() if row["resolved_at"] else None,
    }


async def get_customer_by_email_or_phone(
    conn,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Optional[dict]:
    """Get customer with conversation history by email or phone."""
    customer = None
    if email:
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE email = $1", email
        )
    if not customer and phone:
        customer = await conn.fetchrow(
            "SELECT * FROM customers WHERE phone = $1", phone
        )

    if not customer:
        return None

    conversations = await conn.fetch(
        """
        SELECT c.id, c.initial_channel as channel, c.started_at as created_at,
               (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
        FROM conversations c
        WHERE c.customer_id = $1
        ORDER BY c.started_at DESC
        LIMIT 10
        """,
        customer["id"],
    )

    return {
        "customer_id": str(customer["id"]),
        "email": customer["email"],
        "phone": customer["phone"],
        "name": customer["name"],
        "created_at": customer["created_at"].isoformat(),
        "conversations": [
            {
                "id": str(conv["id"]),
                "channel": conv["channel"],
                "created_at": conv["created_at"].isoformat(),
                "message_count": conv["message_count"],
            }
            for conv in conversations
        ],
    }


async def get_channel_metrics(conn, target_date: datetime) -> dict:
    """Get aggregated metrics by channel for a specific date."""
    metrics = {}

    for channel in ["email", "web_form"]:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(DISTINCT t.id) as total_tickets,
                AVG(c.sentiment_score) as avg_sentiment,
                COUNT(DISTINCT CASE WHEN t.status = 'escalated' THEN t.id END) as escalations,
                AVG(EXTRACT(EPOCH FROM (m.created_at - c.started_at))) as avg_response_time
            FROM tickets t
            JOIN conversations c ON c.id = t.conversation_id
            LEFT JOIN messages m ON m.conversation_id = c.id AND m.direction = 'outgoing'
            WHERE t.source_channel = $1
            AND DATE(t.created_at) = $2
            """,
            channel, target_date.date(),
        )

        metrics[channel] = {
            "total": row["total_tickets"] or 0,
            "avg_sentiment": float(row["avg_sentiment"]) if row["avg_sentiment"] else 0.0,
            "escalations": row["escalations"] or 0,
            "avg_response_time_sec": float(row["avg_response_time"]) if row["avg_response_time"] else 0.0,
        }

    return metrics


async def update_ticket_status(
    conn,
    ticket_id: str,
    status: str,
    resolution_notes: Optional[str] = None,
) -> None:
    """Update ticket status."""
    if status == "resolved":
        await conn.execute(
            """
            UPDATE tickets
            SET status = $1, resolution_notes = $2, resolved_at = NOW()
            WHERE id = $3
            """,
            status, resolution_notes, ticket_id,
        )
    elif status == "escalated":
        await conn.execute(
            """
            UPDATE tickets
            SET status = $1, resolution_notes = $2, escalated_at = NOW()
            WHERE id = $3
            """,
            status, resolution_notes, ticket_id,
        )
    else:
        await conn.execute(
            "UPDATE tickets SET status = $1 WHERE id = $2", status, ticket_id
        )