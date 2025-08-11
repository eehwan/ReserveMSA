import logging
from datetime import datetime
from typing import Callable, Awaitable

from redis.asyncio import Redis

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
    ):
        self.kafka_producer = kafka_producer
        self.redis_client = redis_client

    async def handle_seat_lock_rollback(self, event: SeatLockRollbackEvent):
        """
        seat.lock-rollback 이벤트를 처리합니다.
        Redis에서 해당 좌석의 lock을 해제합니다.
        """
        logger.info(f"[Seat Lock Rollback] Event: {event.event_id}, Seat: {event.seat_num}, Reason: {event.reason}")
        
        redis_key = f"seat:{event.event_id}:{event.seat_num}"
        
        try:
            # Redis에서 lock 해제
            # lock_key가 일치하는 경우에만 삭제하도록 Lua 스크립트 사용
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