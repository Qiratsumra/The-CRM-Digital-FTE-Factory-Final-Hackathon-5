"""Kafka message processor worker."""
from src.kafka.client import FTEKafkaConsumer, FTEKafkaProducer
from src.kafka.topics import TOPICS
from src.database.connection import get_pool, close_pool
from src.database import queries
from src.agent.runner import AgentRunner
from src.agent.whatsapp_agent_runner import WhatsAppAgentRunner
from src.database.queries import create_message
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageProcessor:
    """Process messages from Kafka topics."""

    def __init__(self) -> None:
        self._agent_runner = AgentRunner()
        self._whatsapp_runner = WhatsAppAgentRunner()  # Optimized for WhatsApp
        self._producer = FTEKafkaProducer()

    async def start(self) -> None:
        """Start the message processor worker."""
        logger.info("Starting message processor...")
        
        # Initialize connections
        await get_pool()
        await self._producer.start()
        
        # Create consumer for all inbound topics
        inbound_topics = [
            TOPICS["webform_inbound"],
            TOPICS["email_inbound"],
            TOPICS["whatsapp_inbound"],
        ]

        consumer = FTEKafkaConsumer(inbound_topics, "fte-message-processor")
        await consumer.start()

        logger.info(f"Listening to topics: {inbound_topics}")
        
        # Start consuming messages
        await consumer.consume(self._handle_message)

    async def stop(self) -> None:
        """Stop the message processor."""
        logger.info("Stopping message processor...")
        await self._producer.stop()
        await close_pool()

    async def _handle_message(self, topic: str, message: dict) -> None:
        """
        Handle incoming message from Kafka.

        Args:
            topic: Kafka topic name
            message: Message payload
        """
        try:
            logger.info(f"Processing message from {topic}")
            
            # Extract message data
            ticket_id = message.get("ticket_id")
            customer_id = message.get("customer_id")
            customer_message = message.get("message", "")
            channel = self._get_channel_from_topic(topic)
            
            if not all([ticket_id, customer_id, customer_message]):
                logger.warning(f"Missing required fields in message: {message.keys()}")
                return
            
            logger.info(f"Ticket: {ticket_id}, Customer: {customer_id}, Channel: {channel}")

            # Use WhatsApp-optimized runner for WhatsApp messages (faster)
            if channel == "whatsapp":
                response = await self._whatsapp_runner.process_message(
                    ticket_id=ticket_id,
                    customer_id=customer_id,
                    message=customer_message,
                    channel=channel,
                )
                logger.info(f"WhatsApp quick response generated for ticket {ticket_id}")
            else:
                # Use standard agent for email/web
                response = await self._agent_runner.process_message(
                    ticket_id=ticket_id,
                    customer_id=customer_id,
                    message=customer_message,
                    channel=channel,
                )
                logger.info(f"Agent response generated for ticket {ticket_id}")

            # Store agent response in database (already done by send_response tool)
            # The agent runner's send_response tool handles DB storage
            
            # Publish to metrics topic for tracking
            await self._producer.publish(
                TOPICS["metrics"],
                {
                    "type": "message_processed",
                    "ticket_id": ticket_id,
                    "channel": channel,
                    "response_length": len(response),
                }
            )
            
            # If escalated, publish to escalations topic
            pool = await get_pool()
            async with pool.acquire() as conn:
                ticket = await conn.fetchrow(
                    "SELECT status, resolution_notes FROM tickets WHERE id = $1",
                    ticket_id,
                )
                if ticket and ticket["status"] == "escalated":
                    await self._producer.publish(
                        TOPICS["escalations"],
                        {
                            "ticket_id": ticket_id,
                            "customer_id": customer_id,
                            "reason": ticket["resolution_notes"],
                            "channel": channel,
                        }
                    )
                    logger.info(f"Ticket {ticket_id} escalated - notification sent")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            # Publish to DLQ
            await self._producer.publish(
                TOPICS["dlq"],
                {
                    "original_topic": topic,
                    "error": str(e),
                    "message": message,
                }
            )

    def _get_channel_from_topic(self, topic: str) -> str:
        """Extract channel name from Kafka topic."""
        if "email" in topic:
            return "email"
        elif "whatsapp" in topic:
            return "whatsapp"
        else:
            return "web_form"


async def main():
    """Main entry point for the worker."""
    processor = MessageProcessor()
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())
