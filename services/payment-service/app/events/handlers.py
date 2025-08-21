import json
from typing import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from aiokafka import AIOKafkaProducer
from shared.kafka.topics import PaymentRequestedEvent
from app.services.payment_service import PaymentService

class PaymentEventHandler:
    def __init__(self, kafka_producer: AIOKafkaProducer, db_session_factory: Callable[[], Awaitable[AsyncSession]]):
        self.kafka_producer = kafka_producer
        self.db_session_factory = db_session_factory

    async def handle_payment_requested(self, event: PaymentRequestedEvent):
        """payment_requested 이벤트 처리 - Order Service에서 전송"""
        try:
            print(f"Received payment_requested event: event_id={event.event_id}, seat={event.seat_num}, user={event.user_id}")
            
            # order_id를 lock_key에서 추출 (format: "user_id:order_id")
            order_id = event.lock_key.split(":")[1] if ":" in event.lock_key else event.lock_key
            
            # DB 세션 생성하여 결제 정보 저장
            async for db_session in self.db_session_factory():
                payment_service = PaymentService(db_session, self.kafka_producer)
                payment_key = await payment_service.handle_payment_requested(
                    order_id=order_id, 
                    amount=int(event.amount),
                    event_id=event.event_id,
                    seat_num=event.seat_num
                )
                print(f"Created payment_key: {payment_key} for order_id: {order_id}, event: {event.event_id}, seat: {event.seat_num}, amount: {event.amount}")
                
        except Exception as e:
            print(f"Error handling payment_requested event: {e}")