import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from typing import Callable, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class KafkaConsumerWorker:
    def __init__(
        self,
        topic: str,
        bootstrap_servers: str,
        group_id: str,
        event_model: Type[BaseModel],
        handler: Callable[[BaseModel], None],
        max_retries: int = 20,
        retry_delay: int = 10,
    ):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.event_model = event_model
        self.handler = handler
        self._consumer = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            retry_backoff_ms=5000,
            max_poll_interval_ms=300000,
        )

        for attempt in range(self.max_retries):
            try:
                await self._consumer.start()
                logger.info(f"Consumer for topic '{self.topic}' started successfully.")
                break
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries}: "
                    f"Failed to start consumer for topic '{self.topic}': {e}. "
                    f"Retrying in {self.retry_delay} seconds..."
                )
                if attempt + 1 == self.max_retries:
                    logger.error(f"Could not start consumer for topic '{self.topic}' after {self.max_retries} attempts.")
                    return
                await asyncio.sleep(self.retry_delay)

        try:
            async for msg in self._consumer:
                try:
                    parsed_event = self.event_model(**msg.value)
                    await self.handler(parsed_event)
                except Exception as e:
                    logger.error(f"[ERROR] Failed to parse or handle message in topic '{self.topic}': {e}")
        finally:
            if self._consumer:
                await self._consumer.stop()
                logger.info(f"Consumer for topic '{self.topic}' stopped.")