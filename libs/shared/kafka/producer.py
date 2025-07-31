import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self, bootstrap_servers: str, max_retries: int = 20, retry_delay: int = 10):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def start(self):
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retry_backoff_ms=5000,
            )

        for attempt in range(self.max_retries):
            try:
                await self._producer.start()
                logger.info("Kafka producer started successfully.")
                break
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries}: "
                    f"Failed to start Kafka producer: {e}. "
                    f"Retrying in {self.retry_delay} seconds..."
                )
                if attempt + 1 == self.max_retries:
                    logger.error(f"Could not start Kafka producer after {self.max_retries} attempts.")
                    raise
                await asyncio.sleep(self.retry_delay)

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped.")

    async def send(self, topic: str, message: dict):
        if not self._producer:
            raise RuntimeError("Producer not started")
        await self._producer.send_and_wait(topic, message)