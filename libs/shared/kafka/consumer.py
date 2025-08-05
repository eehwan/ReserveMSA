import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from typing import Callable, Type, Awaitable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 개별 토픽용 워커 클래스
class KafkaConsumerWorker:
    def __init__(
        self,
        topic: str,
        bootstrap_servers: str,
        group_id: str,
        event_model: Type[BaseModel],
        handler: Callable[[BaseModel], Awaitable[None]],
        max_retries: int = 20,
        retry_delay: int = 5,
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


# 여러 토픽을 관리하는 공통 매니저 클래스
class BaseKafkaConsumerManager:
    def __init__(self, topic_handlers: dict[str, Callable], group_id: str, bootstrap_servers: str):
        self.topic_handlers = topic_handlers
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.tasks: list[asyncio.Task] = []

    def _create_worker(self, topic_key: str) -> KafkaConsumerWorker:
        from .topics import TOPICS  # 순환참조 방지용 내부 import
        topic_info = TOPICS[topic_key]
        return KafkaConsumerWorker(
            topic=topic_info["topic"],
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            event_model=topic_info["schema"],
            handler=self.topic_handlers[topic_key],
        )

    async def start(self):
        for topic_key in self.topic_handlers:
            worker = self._create_worker(topic_key)
            task = asyncio.create_task(worker.start())
            self.tasks.append(task)
        logger.info(f"[Kafka] Started {len(self.tasks)} consumer workers.")

    async def stop(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("[Kafka] All consumer workers stopped.")
