"""AI Agent runner using Gemini SDK directly."""
import google.generativeai as genai
from src.database.connection import get_pool
from src.skills.sentiment_analysis import analyze_sentiment
from src.skills.escalation_decision import decide_escalation
from src.agent.formatters import Channel, truncate_to_words
from src.config import get_settings
import json
import logging
import re

logger = logging.getLogger(__name__)
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)


class AgentRunner:
    """Run the Customer Success FTE agent using Gemini."""

    def __init__(self) -> None:
        self._model = genai.GenerativeModel(settings.gemini_model)

    async def process_message(
        self,
        ticket_id: str,
        customer_id: str,
        message: str,
        channel: str,
    ) -> str:
        """
        Process incoming message through the AI agent.

        Args:
            ticket_id: Ticket UUID
            customer_id: Customer UUID
            message: Customer message text
            channel: Channel name (email, web_form, whatsapp)

        Returns:
            Agent response text or escalation notice
        """
        try:
            # Step 1: Analyze sentiment
            sentiment = await analyze_sentiment(message)
            logger.info(f"Sentiment score: {sentiment.score} ({sentiment.label})")

            # Step 2: Check for immediate escalation
            escalation = decide_escalation(message, sentiment.score)
            if escalation.should_escalate:
                logger.info(f"Escalation triggered: {escalation.reason}")
                await self._escalate_ticket(ticket_id, escalation.reason)
                return self._get_escalation_response(channel)

            # Step 3: Build context with customer history and knowledge base
            context = await self._build_context(customer_id, message, channel)

            # Step 4: Generate response using Gemini
            response = await self._generate_response(context, message, channel)
            
            # Step 5: Send response via tool (stores in DB)
            await self._send_response(ticket_id, response, channel)
            
            logger.info(f"Agent response generated: {len(response)} chars")
            return response


        except Exception as e:
            logger.error(f"Agent processing failed: {e}", exc_info=True)
            # Fallback: escalate to human
            await self._escalate_ticket(ticket_id, "agent_error")
            return "An error occurred. Escalating to human support."

    async def _build_context(
        self, customer_id: str, message: str, channel: str
    ) -> str:
        """Build context for agent including customer history."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Get customer info
            customer = await conn.fetchrow(
                "SELECT email, phone, name FROM customers WHERE id = $1", customer_id
            )

            # Get recent conversation history
            history_rows = await conn.fetch(
                """
                SELECT m.content, m.direction, m.channel, m.created_at
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.customer_id = $1
                ORDER BY m.created_at DESC
                LIMIT 5
                """,
                customer_id,
            )
            
            # Search knowledge base
            kb_results = await self._search_knowledge_base(message)

        history = "\n".join(
            f"[{r['direction'].upper()} via {r['channel']}] {r['content'][:150]}"
            for r in history_rows
        ) if history_rows else "No previous conversations."

        customer_name = customer["name"] or "Customer"
        customer_email = customer["email"] or customer["phone"] or "Unknown"

        return f"""
Customer: {customer_name} ({customer_email})
Channel: {channel}
Current Message: {message}

Recent History:
{history}

Knowledge Base Results:
{kb_results}

You are a helpful Qirat Saeed AI Support agent. Provide accurate, friendly responses.
"""

    async def _search_knowledge_base(self, query: str) -> str:
        """Search knowledge base for relevant articles."""
        try:
            # Generate embedding using correct Gemini model
            embedding_result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query
            )
            embedding = embedding_result.get("embedding", [])
            
            if not embedding:
                return "No knowledge base results."
            
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
                    ORDER BY embedding <=> $1::vector
                    LIMIT 3
                    """,
                    embedding_json,
                )
                
                if not results:
                    return "No relevant documentation found."
                
                return "\n\n".join(
                    f"**{r['title']}** (relevance: {r['similarity']:.2f})\n{r['content'][:300]}"
                    for r in results
                )
        except Exception as e:
            logger.error(f"KB search failed: {e}")
            return "Knowledge base search unavailable."

    async def _generate_response(self, context: str, message: str, channel: str) -> str:
        """Generate response using Gemini."""
        # Build prompt with channel-specific instructions
        channel_instructions = {
            "email": "Include a greeting (Dear/Hello) and professional signature. Keep under 500 words.",
            "web_form": "Keep response under 300 words. Be clear and helpful.",
        }
        
        prompt = f"""
{context}

Please provide a helpful response to the customer's message.

Channel-specific requirements:
{channel_instructions.get(channel, "Be concise and helpful.")}

If the question is about product features, use the knowledge base results above.
If you cannot help or the customer is upset, suggest escalation to human support.

Response:
"""
        
        try:
            response = await self._model.generate_content_async(prompt)
            text = response.text.strip()

            # Apply channel-specific truncation
            if channel == "web_form":
                text = truncate_to_words(text, 300)
            elif channel == "email":
                text = truncate_to_words(text, 500)

            return text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response. Let me connect you to a human agent."

    async def _send_response(self, ticket_id: str, content: str, channel: str) -> None:
        """Store response in database and send email for web form and email tickets."""
        from src.agent.formatters import format_for_channel
        from src.channels.sendgrid_sender import get_sendgrid_sender
        from src.channels.gmail_handler import GmailHandler
        from src.channels.whatsapp_handler import WhatsAppHandler
        from src.database.connection import get_pool
        from src.kafka.client import FTEKafkaProducer
        from src.config import get_settings

        pool = await get_pool()
        settings = get_settings()

        async with pool.acquire() as conn:
            # Get conversation_id and customer info
            row = await conn.fetchrow(
                """
                SELECT c.id as conversation_id, cust.email, cust.phone, cust.name, t.source_channel as channel
                FROM tickets t
                JOIN conversations c ON c.id = t.conversation_id
                JOIN customers cust ON cust.id = t.customer_id
                WHERE t.id = $1
                """,
                ticket_id,
            )

            if not row:
                raise ValueError(f"Ticket {ticket_id} not found")

            conversation_id = str(row["conversation_id"])
            customer_email = row["email"]
            customer_phone = row["phone"]
            customer_name = row["name"]
            ticket_channel = row["channel"]

            # Format response for channel
            formatted = format_for_channel(content, Channel(ticket_channel), ticket_id)

            # Store outgoing message in database
            await conn.execute(
                """
                INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status)
                VALUES ($1, $2, 'outgoing', 'agent', $3, 'pending')
                """,
                conversation_id, ticket_channel, formatted,
            )

            # Update ticket status
            await conn.execute(
                "UPDATE tickets SET status = 'resolved', resolved_at = NOW() WHERE id = $1",
                ticket_id,
            )

            # Send response for all channels
            if ticket_channel == "whatsapp" and customer_phone:
                # Send via WhatsApp MCP
                logger.info(f"Sending response via WhatsApp MCP for ticket {ticket_id}")
                logger.info(f"Customer phone: {customer_phone}, MCP enabled: {settings.whatsapp_mcp_enabled}")

                if settings.whatsapp_mcp_enabled:
                    try:
                        producer = FTEKafkaProducer()
                        whatsapp_handler = WhatsAppHandler(producer=producer)
                        initialized = await whatsapp_handler.initialize()

                        logger.info(f"WhatsApp handler initialized: {initialized}")

                        if initialized:
                            success = await whatsapp_handler.send_response(ticket_id, content, customer_phone)
                            logger.info(f"WhatsApp MCP response sent: {success} to {customer_phone}")
                            if success:
                                # Update delivery status
                                await conn.execute(
                                    """
                                    UPDATE messages SET delivery_status = 'sent'
                                    WHERE id = (
                                        SELECT id FROM messages
                                        WHERE conversation_id = $1 AND direction = 'outgoing'
                                        ORDER BY created_at DESC LIMIT 1
                                    )
                                    """,
                                    conversation_id,
                                )
                            else:
                                logger.warning(f"WhatsApp MCP send_response returned False - check bridge status")
                        else:
                            logger.warning(f"WhatsApp MCP not initialized, message stored in DB only")
                            logger.warning(f"Start the Go bridge: cd whatsapp-mcp/whatsapp-bridge && go run main.go")

                        await whatsapp_handler.close()
                        await producer.stop()
                    except Exception as e:
                        logger.error(f"Failed to send WhatsApp response: {e}", exc_info=True)
                        await conn.execute(
                            """
                            UPDATE messages SET delivery_status = 'failed'
                            WHERE id = (
                                SELECT id FROM messages
                                WHERE conversation_id = $1 AND direction = 'outgoing'
                                ORDER BY created_at DESC LIMIT 1
                            )
                            """,
                            conversation_id,
                        )
                else:
                    logger.info(f"WhatsApp MCP disabled in settings, message stored in DB only")
                    logger.info(f"To enable, set WHATSAPP_MCP_ENABLED=true in .env")

            elif customer_email:
                # Send email for ALL channels including web_form
                logger.info(f"📧 Sending email response for ticket {ticket_id} to {customer_email}")

                # Get the first incoming message as subject (truncated)
                message_row = await conn.fetchrow(
                    """
                    SELECT content FROM messages
                    WHERE conversation_id = $1 AND direction = 'incoming'
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    conversation_id,
                )
                subject = message_row["content"][:50] + "..." if message_row else "Support Request"

                email_sent = False

                # Try SendGrid first (works on Render - uses HTTPS not SMTP)
                try:
                    logger.info(f"Attempting SendGrid send to {customer_email}")
                    email_sender = get_sendgrid_sender()
                    email_sent = await email_sender.send_ticket_response(
                        to_email=customer_email,
                        ticket_id=ticket_id,
                        subject=subject,
                        response=formatted,
                        customer_name=customer_name,
                    )

                    if email_sent:
                        logger.info(f"✅ Email sent successfully via SendGrid to {customer_email}")
                        # Update delivery status
                        await conn.execute(
                            """
                            UPDATE messages SET delivery_status = 'sent'
                            WHERE id = (
                                SELECT id FROM messages
                                WHERE conversation_id = $1 AND direction = 'outgoing'
                                ORDER BY created_at DESC LIMIT 1
                            )
                            """,
                            conversation_id,
                        )
                    else:
                        logger.warning(f"⚠️ SendGrid send returned False - API key may be missing")
                        # Trigger Gmail API fallback
                        raise Exception("SendGrid failed - falling back to Gmail API")

                except Exception as sendgrid_error:
                    logger.error(f"❌ SendGrid sending failed: {sendgrid_error}", exc_info=False)

                    # Try Gmail API as fallback
                    try:
                        logger.info(f"Attempting Gmail API fallback for {customer_email}")
                        producer = FTEKafkaProducer()
                        gmail_handler = GmailHandler(producer)

                        email_sent = await gmail_handler.send_reply(
                            thread_id=conversation_id,
                            content=formatted,
                            in_reply_to=str(ticket_id),
                            to_email=customer_email,
                        )

                        if email_sent:
                            logger.info(f"✅ Email sent successfully via Gmail API to {customer_email}")
                            await conn.execute(
                                """
                                UPDATE messages SET delivery_status = 'sent'
                                WHERE id = (
                                    SELECT id FROM messages
                                    WHERE conversation_id = $1 AND direction = 'outgoing'
                                    ORDER BY created_at DESC LIMIT 1
                                )
                                """,
                                conversation_id,
                            )
                        else:
                            logger.warning(f"⚠️ Gmail API also failed")

                    except Exception as gmail_error:
                        logger.error(f"❌ Gmail API fallback also failed: {gmail_error}", exc_info=False)

                # Mark as failed if both methods failed
                if not email_sent:
                    await conn.execute(
                        """
                        UPDATE messages SET delivery_status = 'failed'
                        WHERE id = (
                            SELECT id FROM messages
                            WHERE conversation_id = $1 AND direction = 'outgoing'
                            ORDER BY created_at DESC LIMIT 1
                        )
                        """,
                        conversation_id,
                    )
                    logger.error(f"❌ All email sending methods failed for {customer_email}")

    async def _escalate_ticket(self, ticket_id: str, reason: str) -> None:
        """Escalate ticket to human support."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE tickets 
                SET status = 'escalated', resolution_notes = $1
                WHERE id = $2
                """,
                f"Escalation reason: {reason}",
                ticket_id,
            )

    def _get_escalation_response(self, channel: str) -> str:
        """Get appropriate escalation response for channel."""
        if channel == "email":
            return "Your inquiry requires specialized assistance. A human agent will respond to your email within 2 hours."
        else:  # web_form
            return "I'm connecting you to a human specialist. They'll review your case and respond promptly."
