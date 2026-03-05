"""WhatsApp channel handler for MCP-based message processing."""
from src.database.connection import get_pool
from src.database import queries
from src.kafka.client import FTEKafkaProducer
from src.kafka.topics import TOPICS
from src.config import get_settings
from src.channels.whatsapp_mcp_client import WhatsAppMCPClient, WhatsAppMessage
import logging
from typing import Optional, Dict, Any
import re

logger = logging.getLogger(__name__)
settings = get_settings()


class WhatsAppHandler:
    """Handle WhatsApp MCP messages for customer support."""

    def __init__(self, producer: FTEKafkaProducer, mcp_client: Optional[WhatsAppMCPClient] = None):
        self._producer = producer
        self._mcp_client = mcp_client
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize WhatsApp MCP client."""
        try:
            if not self._mcp_client:
                bridge_path = settings.whatsapp_mcp_bridge_path
                self._mcp_client = WhatsAppMCPClient(bridge_path=bridge_path)
            
            self._initialized = await self._mcp_client.initialize()
            if self._initialized:
                logger.info("WhatsApp MCP handler initialized")
            else:
                logger.warning("WhatsApp MCP handler initialization failed")
            return self._initialized
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp MCP handler: {e}")
            return False

    async def close(self):
        """Close MCP client connection."""
        if self._mcp_client:
            await self._mcp_client.close()
            logger.info("WhatsApp MCP handler closed")

    async def process_inbound_message(self, phone_number: str, message_text: str) -> Optional[str]:
        """
        Process incoming WhatsApp message.

        Args:
            phone_number: Phone number in E.164 format (e.g., +923001234567)
            message_text: Message content

        Returns:
            Ticket ID if successful
        """
        try:
            pool = await get_pool()
            
            # Create or get customer by phone
            customer_id = await self._create_or_get_customer(pool, phone_number)
            
            # Create ticket
            ticket_id = await self._create_ticket(pool, customer_id, "WhatsApp Support")
            
            # Store incoming message
            await self._store_message(pool, ticket_id, message_text, "incoming")
            
            # Publish to Kafka for agent processing
            await self._producer.publish(
                TOPICS["whatsapp_inbound"],
                {
                    "ticket_id": str(ticket_id),
                    "customer_id": str(customer_id),
                    "from": phone_number,
                    "message": message_text,
                    "channel": "whatsapp",
                }
            )
            
            logger.info(f"Processed WhatsApp message from {phone_number}: {message_text[:50]}...")
            return str(ticket_id)
            
        except Exception as e:
            logger.error(f"Failed to process WhatsApp message: {e}")
            return None

    async def send_response(self, ticket_id: str, response_text: str, to_phone: str) -> bool:
        """
        Send WhatsApp response via MCP.

        Args:
            ticket_id: Ticket ID
            response_text: Response content (will be truncated to 300 chars)
            to_phone: Recipient phone number

        Returns:
            True if successful
        """
        try:
            if not self._initialized or not self._mcp_client:
                logger.warning("WhatsApp MCP handler not initialized")
                return False
            
            # Truncate for WhatsApp (300 char limit)
            truncated_response = response_text[:300]
            
            # Send via MCP
            success = await self._mcp_client.send_message(to_phone, truncated_response)
            
            if success:
                # Store outgoing message in our database
                pool = await get_pool()
                async with pool.acquire() as conn:
                    ticket = await queries.get_ticket(conn, ticket_id)
                    if ticket:
                        await queries.store_message(
                            conn,
                            conversation_id=ticket["conversation_id"],
                            channel="whatsapp",
                            direction="outgoing",
                            role="support",
                            content=truncated_response,
                        )
                
                logger.info(f"Sent WhatsApp response to {to_phone}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp response: {e}")
            return False

    async def _create_or_get_customer(self, pool, phone_number: str) -> str:
        """Create or get customer by phone number."""
        async with pool.acquire() as conn:
            # Check if customer exists by phone
            customer = await queries.get_customer_by_phone(conn, phone_number)

            if customer:
                return customer["id"]

            # Create new customer
            customer_id = await queries.create_customer(
                conn,
                email=None,  # Email may be added later
                phone=phone_number,
                name=f"WhatsApp User {phone_number[-4:]}",
            )
            return customer_id

    async def _create_ticket(self, pool, customer_id: str, subject: str) -> str:
        """Create support ticket."""
        async with pool.acquire() as conn:
            # Create conversation
            conversation_id = await queries.create_conversation(
                conn,
                customer_id=customer_id,
                channel="whatsapp",
            )
            
            # Create ticket
            ticket_id = await queries.create_ticket(
                conn,
                conversation_id=conversation_id,
                customer_id=customer_id,
                source_channel="whatsapp",
                category="support",
            )
            
            return ticket_id

    async def _store_message(
        self,
        pool,
        ticket_id: str,
        content: str,
        direction: str = "incoming",
    ):
        """Store message in database."""
        async with pool.acquire() as conn:
            ticket = await queries.get_ticket(conn, ticket_id)
            if ticket:
                await queries.store_message(
                    conn,
                    conversation_id=ticket["conversation_id"],
                    channel="whatsapp",
                    direction=direction,
                    role="customer" if direction == "incoming" else "support",
                    content=content,
                )

    async def poll_messages(self) -> list:
        """
        Poll for new WhatsApp messages.

        Returns:
            List of processed message info
        """
        if not self._initialized or not self._mcp_client:
            return []
        
        processed = []
        try:
            # Get all chats
            chats = await self._mcp_client._db_client.get_all_chats() if self._mcp_client._db_client else []
            
            for chat in chats:
                chat_jid = chat["jid"]
                # Extract phone number from JID
                phone_number = "+" + chat_jid.replace("@s.whatsapp.net", "")
                
                # Get unread messages
                unread = await self._mcp_client._db_client.get_unread_messages(chat_jid) if self._mcp_client._db_client else []
                
                for msg in unread:
                    if not msg.is_from_me and msg.message_text:
                        ticket_id = await self.process_inbound_message(phone_number, msg.message_text)
                        if ticket_id:
                            # Mark as read
                            await self._mcp_client._db_client.mark_message_read(msg.id) if self._mcp_client._db_client else None
                            processed.append({
                                "phone": phone_number,
                                "ticket_id": ticket_id,
                                "message": msg.message_text[:50],
                            })
            
            if processed:
                logger.info(f"Processed {len(processed)} WhatsApp messages")
            
            return processed
            
        except Exception as e:
            logger.error(f"Failed to poll WhatsApp messages: {e}")
            return []

    async def check_bridge_status(self) -> bool:
        """Check if Go bridge is running."""
        if not self._mcp_client:
            return False
        return await self._mcp_client.check_go_bridge_status()
