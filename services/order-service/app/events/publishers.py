from shared.kafka.producer import KafkaProducer
from shared.kafka.topics import (
    TOPICS, 
    SeatLockEvent, 
    SeatLockFailedEvent, 
    SeatUnlockEvent, 
    PaymentTimeoutEvent,
    PaymentRequestedEvent
)
from datetime import datetime

class OrderEventPublisher:
    def __init__(self, kafka_producer: KafkaProducer):
        self.kafka_producer = kafka_producer
    
    async def publish_seat_lock(self, order_id: str, user_id: int, event_id: int, seat_num: str, lock_key: str, expires_at: datetime):
        """좌석 선점 성공 이벤트 발행"""
        event = SeatLockEvent(
            order_id=order_id,
            user_id=user_id,
            event_id=event_id,
            seat_num=seat_num,
            lock_key=lock_key,
            expires_at=expires_at,
            timestamp=datetime.utcnow(),
        )
        await self.kafka_producer.send(
            topic=TOPICS["seat_lock"]["topic"],
            message=event.model_dump(mode="json")
        )
    
    async def publish_seat_lock_failed(self, user_id: int, event_id: int, seat_num: str, reason: str):
        """좌석 선점 실패 이벤트 발행"""
        event = SeatLockFailedEvent(
            user_id=user_id,
            event_id=event_id,
            seat_num=seat_num,
            reason=reason,
            timestamp=datetime.utcnow(),
        )
        await self.kafka_producer.send(
            topic=TOPICS["seat_lock_failed"]["topic"],
            message=event.model_dump(mode="json")
        )
    
    async def publish_seat_unlock(self, event_id: int, seat_num: str, lock_key: str):
        """좌석 선점 취소 이벤트 발행"""
        event = SeatUnlockEvent(
            event_id=event_id,
            seat_num=seat_num,
            lock_key=lock_key,
            timestamp=datetime.utcnow(),
        )
        await self.kafka_producer.send(
            topic=TOPICS["seat_unlock"]["topic"],
            message=event.model_dump(mode="json")
        )
    
    async def publish_payment_timeout(self, event_id: int, seat_num: str, lock_key: str):
        """결제 타임아웃 이벤트 발행"""
        event = PaymentTimeoutEvent(
            user_id=0,  # celery task에서는 user_id 추적 어려움
            event_id=event_id,
            seat_num=seat_num,
            lock_key=lock_key,
            timeout_duration=0,  # 실제 timeout duration은 consumer에서 처리
            timestamp=datetime.utcnow(),
        )
        await self.kafka_producer.send(
            topic=TOPICS["payment_timeout"]["topic"],
            message=event.model_dump(mode="json")
        )
    
    async def publish_payment_requested(self, order_id: str, user_id: int, event_id: int, seat_num: str, amount: float, lock_key: str):
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