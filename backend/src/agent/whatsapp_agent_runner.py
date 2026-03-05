"""
WhatsApp Agent Runner - Optimized for Speed and Accuracy

Uses quick answers for common questions, fallback to full AI for complex queries.
"""
import google.generativeai as genai
from src.database.connection import get_pool
from src.skills.sentiment_analysis import analyze_sentiment
from src.skills.escalation_decision import decide_escalation
from src.skills.quick_answer import get_quick_answer, handle_greeting, handle_thanks
from src.agent.formatters import Channel, truncate_to_words
from src.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)


class WhatsAppAgentRunner:
    """
    Optimized agent runner for WhatsApp.
    
    Strategy:
    1. Try quick answers first (instant response)
    2. Use AI only for complex queries
    3. Always escalate for sensitive topics
    """

    def __init__(self) -> None:
        self._model = genai.GenerativeModel(settings.gemini_model)

    async def process_message(
        self,
        ticket_id: str,
        customer_id: str,
        message: str,
        channel: str = "whatsapp",
    ) -> str:
        """
        Process WhatsApp message with speed optimization.

        Args:
            ticket_id: Ticket UUID
            customer_id: Customer UUID
            message: Customer message text
            channel: Channel name (should be "whatsapp")

        Returns:
            Agent response text or escalation notice
        """
        try:
            # Step 1: Check for quick answer (FAST - <100ms)
            quick_answer = await get_quick_answer(message)
            
            if quick_answer:
                logger.info(f"Quick answer matched: {quick_answer['intent']}")
                
                # Handle escalation if needed
                if quick_answer.get("escalate"):
                    await self._escalate_ticket(ticket_id, f"quick_answer_{quick_answer['intent']}")
                
                # Send response
                await self._send_response(ticket_id, quick_answer["response"], channel)
                return quick_answer["response"]

            # Step 2: Handle greetings (instant)
            greeting = handle_greeting(message)
            if greeting:
                await self._send_response(ticket_id, greeting, channel)
                return greeting

            # Step 3: Handle thanks (instant)
            thanks = handle_thanks(message)
            if thanks:
                await self._send_response(ticket_id, thanks, channel)
                return thanks

            # Step 4: Analyze sentiment (for escalation detection)
            sentiment = await analyze_sentiment(message)
            logger.info(f"Sentiment: {sentiment.score} ({sentiment.label})")

            # Step 5: Check for immediate escalation
            escalation = decide_escalation(message, sentiment.score)
            if escalation.should_escalate:
                logger.info(f"Escalation triggered: {escalation.reason}")
                await self._escalate_ticket(ticket_id, escalation.reason)
                return self._get_escalation_response(channel)

            # Step 6: Build context for AI (only for complex queries)
            context = await self._build_context(customer_id, message, channel)

            # Step 7: Generate AI response
            response = await self._generate_response(context, message, channel)

            # Step 8: Send response
            await self._send_response(ticket_id, response, channel)

            logger.info(f"AI response generated: {len(response)} chars")
            return response

        except Exception as e:
            logger.error(f"Agent processing failed: {e}", exc_info=True)
            # Fallback: escalate to human
            await self._escalate_ticket(ticket_id, "agent_error")
            return "I apologize, but I'm having trouble. Let me connect you to a human agent."

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

            # Get recent conversation history (last 3 messages for speed)
            history_rows = await conn.fetch(
                """
                SELECT m.content, m.direction, m.channel, m.created_at
                FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.customer_id = $1
                ORDER BY m.created_at DESC
                LIMIT 3
                """,
                customer_id,
            )

            # Search knowledge base
            kb_results = await self._search_knowledge_base(message)

        history = "\n".join(
            f"[{r['direction'].upper()} via {r['channel']}] {r['content'][:100]}"
            for r in history_rows
        ) if history_rows else "First contact."

        customer_name = customer["name"] or "Customer"
        customer_email = customer["email"] or customer["phone"] or "Unknown"

        return f"""
Customer: {customer_name} ({customer_email})
Channel: {channel}
Message: {message}

Recent History:
{history}

Knowledge Base:
{kb_results}

You are a helpful Qirat Saeed AI Support agent. Be concise and accurate.
"""

    async def _search_knowledge_base(self, query: str) -> str:
        """Search knowledge base for relevant articles."""
        try:
            # Generate embedding
            embedding_result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query
            )
            embedding = embedding_result.get("embedding", [])

            if not embedding:
                return "No KB results."

            pool = await get_pool()
            async with pool.acquire() as conn:
                import json
                embedding_json = json.dumps(embedding)

                results = await conn.fetch(
                    """
                    SELECT title, content, category,
                           1 - (embedding <=> $1::vector) as similarity
                    FROM knowledge_base
                    ORDER BY embedding <=> $1::vector
                    LIMIT 2
                    """,
                    embedding_json,
                )

                if not results:
                    return "No relevant docs found."

                return "\n".join(
                    f"{r['title']}: {r['content'][:200]}"
                    for r in results
                )
        except Exception as e:
            logger.error(f"KB search failed: {e}")
            return "KB search unavailable."

    async def _generate_response(self, context: str, message: str, channel: str) -> str:
        """Generate response using Gemini - optimized for WhatsApp."""
        prompt = f"""
{context}

Generate a WhatsApp response:
- MAX 300 characters (WhatsApp limit)
- Be direct and helpful
- No greeting/signature needed
- If unsure, suggest escalation

Customer message: {message}

Response:"""

        try:
            response = await self._model.generate_content_async(prompt)
            text = response.text.strip()

            # Truncate for WhatsApp (hard limit)
            text = truncate_to_words(text, 50)  # ~300 chars
            
            return text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return "I apologize, but I'm having trouble. Let me connect you to a human agent."

    async def _send_response(self, ticket_id: str, content: str, channel: str) -> None:
        """Store response in database and send via WhatsApp."""
        from src.channels.whatsapp_handler import WhatsAppHandler
        from src.database.connection import get_pool
        from src.kafka.client import FTEKafkaProducer

        pool = await get_pool()

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
            customer_phone = row["phone"]

            # Store outgoing message in database
            await conn.execute(
                """
                INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status)
                VALUES ($1, $2, 'outgoing', 'agent', $3, 'sent')
                """,
                conversation_id, channel, content,
            )

            # Update ticket status
            await conn.execute(
                "UPDATE tickets SET status = 'resolved', resolved_at = NOW() WHERE id = $1",
                ticket_id,
            )

            # Send via WhatsApp if phone available
            if channel == "whatsapp" and customer_phone:
                logger.info(f"Sending WhatsApp response for ticket {ticket_id}")

                if settings.whatsapp_mcp_enabled:
                    try:
                        producer = FTEKafkaProducer()
                        whatsapp_handler = WhatsAppHandler(producer=producer)
                        initialized = await whatsapp_handler.initialize()

                        if initialized:
                            success = await whatsapp_handler.send_response(ticket_id, content, customer_phone)
                            logger.info(f"WhatsApp sent: {success}")
                            if not success:
                                logger.warning(f"WhatsApp send returned False")

                        await whatsapp_handler.close()
                        await producer.stop()
                    except Exception as e:
                        logger.error(f"Failed to send WhatsApp: {e}", exc_info=True)
                else:
                    logger.info("WhatsApp MCP disabled, stored in DB only")

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
        """Get escalation response for WhatsApp."""
        return "I'm connecting you to a human specialist. They'll review your case and respond promptly."
