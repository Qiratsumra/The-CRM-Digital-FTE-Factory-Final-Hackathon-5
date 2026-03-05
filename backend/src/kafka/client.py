"""Kafka producer and consumer clients."""
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from src.config import get_settings
from datetime import datetime
import asyncio
import json
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class FTEKafkaProducer:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None
        self._connected = False

    async def start(self) -> None:
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
            self._connected = True
            logger.info("Kafka producer started")
        except Exception as e:
            logger.warning(f"Kafka not available, running without Kafka: {e}")
            self._connected = False

    async def stop(self) -> None:
        if self._producer and self._connected:
            await self._producer.stop()

    async def publish(self, topic: str, event: dict) -> None:
        if not self._connected:
            logger.debug(f"Kafka not connected, skipping publish to {topic}")
            return
        event["timestamp"] = datetime.utcnow().isoformat()
        try:
            await self._producer.send_and_wait(topic, event)
        except Exception as e:
            logger.warning(f"Failed to publish to {topic}: {e}")


class FTEKafkaConsumer:
    def __init__(self, topics: list[str], group_id: str) -> None:
        self._topics = topics
        self._group_id = group_id
        self._consumer: AIOKafkaConsumer | None = None
        self._connected = False

    async def start(self) -> None:
        try:
            self._consumer = AIOKafkaConsumer(
                *self._topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=self._group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
            )
            await self._consumer.start()
            self._connected = True
            logger.info(f"Kafka consumer started for group: {self._group_id}")
        except Exception as e:
            logger.warning(f"Kafka not available, running without Kafka: {e}")
            self._consumer = None
            self._connected = False

    async def stop(self) -> None:
        if self._consumer and self._connected:
            await self._consumer.stop()

    async def consume(self, handler) -> None:
        if not self._connected or not self._consumer:
            logger.warning("Kafka not connected - running in no-op mode")
            while True:
                await asyncio.sleep(5)
            return
        async for msg in self._consumer:
            try:
                await handler(msg.topic, msg.value)
            except Exception as e:
                logger.error(f"Handler error on {msg.topic}: {e}")
