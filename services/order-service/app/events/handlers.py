import logging
from typing import Callable, Awaitable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from shared.kafka.producer import KafkaProducer
from shared.kafka.topics import (
    TOPICS,
    SeatLockRollbackEvent,
)

logger = logging.getLogger(__name__)

class OrderEventHandler:
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        redis_client: Redis,
        db_session_factory: Callable[[], Awaitable[AsyncSession]],
    ):
        self.kafka_producer = kafka_producer
        self.redis_client = redis_client
        self.db_session_factory = db_session_factory

    async def handle_seat_lock_rollback(self, event: SeatLockRollbackEvent):
        """
        seat.lock-rollback 이벤트를 처리합니다.
        Redis 락만 해제하고, 주문서는 그대로 유지합니다.
        """
        logger.info(f"[Seat Lock Rollback] Event: {event.event_id}, Seat: {event.seat_num}, Reason: {event.reason}")
        
        redis_key = f"seat:{event.event_id}:{event.seat_num}"
        
        try:
            # Redis에서 락 해제 (lock_key가 일치하는 경우에만)
            lua_script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
            """
            result = await self.redis_client.eval(lua_script, 1, redis_key, event.lock_key)
            
            if result == 1:
                logger.info(f"Successfully released Redis lock for seat {event.seat_num}")
            else:
                logger.warning(f"Lock key mismatch or already released for seat {event.seat_num}")
                
        except Exception as e:
            logger.error(f"Failed to release Redis lock for seat {event.seat_num}: {e}")