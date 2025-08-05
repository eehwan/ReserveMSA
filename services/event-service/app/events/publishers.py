from shared.kafka.producer import KafkaProducer
from shared.kafka.topics import (
    TOPICS,
    PaymentRequestedEvent,
    SeatLockRollbackEvent,
)
from datetime import datetime

class EventServicePublisher:
    def __init__(self, kafka_producer: KafkaProducer):
        self.kafka_producer = kafka_producer
    
    async def publish_payment_requested(self, user_id: int, event_id: int, seat_num: str, amount: float, lock_key: str):
        """결제 요청 이벤트 발행"""
        event = PaymentRequestedEvent(
            user_id=user_id,
            event_id=event_id,
            seat_num=seat_num,
            amount=amount,
            lock_key=lock_key,
            timestamp=datetime.utcnow(),
        )
        await self.kafka_producer.send(
            topic=TOPICS["payment_requested"]["topic"],
            message=event.model_dump(mode="json")
        )
    
    async def publish_seat_lock_rollback(self, event_id: int, seat_num: str, lock_key: str, reason: str):
        """좌석 선점 롤백 이벤트 발행"""
        event = SeatLockRollbackEvent(
            event_id=event_id,
            seat_num=seat_num,
            lock_key=lock_key,
            reason=reason,
            timestamp=datetime.utcnow(),
        )
        await self.kafka_producer.send(
            topic=TOPICS["seat_lock_rollback"]["topic"],
            message=event.model_dump(mode="json")
        )