"""
WhatsApp MCP Worker - Polls for new messages

This worker periodically checks the WhatsApp MCP database for new messages
and processes them through the customer support system.

Usage:
    python -m src.workers.whatsapp_worker
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from src.config import get_settings
from src.channels.whatsapp_handler import WhatsAppHandler
from src.kafka.client import FTEKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


class WhatsAppWorker:
    """Worker that polls WhatsApp MCP for new messages."""

    def __init__(self):
        self._handler: WhatsAppHandler | None = None
        self._producer: FTEKafkaProducer | None = None
        self._running = False
        self._poll_interval = settings.whatsapp_poll_interval

    async def start(self):
        """Start the WhatsApp worker."""
        logger.info("Starting WhatsApp MCP worker...")

        # Initialize Kafka producer
        self._producer = FTEKafkaProducer()
        await self._producer.start()

        # Initialize WhatsApp handler
        self._handler = WhatsAppHandler(producer=self._producer)
        initialized = await self._handler.initialize()

        if not initialized:
            logger.error("Failed to initialize WhatsApp handler. Worker will not poll messages.")
            if settings.whatsapp_mcp_enabled:
                logger.warning("WhatsApp MCP is enabled but handler initialization failed")
            return

        # Check Go bridge status
        bridge_status = await self._handler.check_bridge_status()
        if not bridge_status:
            logger.warning(
                "Go bridge not detected. Messages will be stored locally but not sent to WhatsApp servers. "
                "To enable sending, start the Go bridge: cd whatsapp-mcp/whatsapp-bridge && go run main.go"
            )

        self._running = True
        logger.info(f"WhatsApp MCP worker started (poll interval: {self._poll_interval}s)")

        # Main polling loop
        while self._running:
            try:
                # Poll for new messages
                processed = await self._handler.poll_messages()

                if processed:
                    logger.info(f"Processed {len(processed)} new WhatsApp message(s)")
                    for msg in processed:
                        logger.info(f"  - {msg['phone']}: {msg['message']}... (ticket: {msg['ticket_id']})")

            except Exception as e:
                logger.error(f"Error polling WhatsApp messages: {e}")

            # Wait for next poll
            await asyncio.sleep(self._poll_interval)

    async def stop(self):
        """Stop the WhatsApp worker."""
        logger.info("Stopping WhatsApp MCP worker...")
        self._running = False

        if self._handler:
            await self._handler.close()

        if self._producer:
            await self._producer.stop()

        logger.info("WhatsApp MCP worker stopped")


async def main():
    """Main entry point."""
    worker = WhatsAppWorker()

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(worker.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
