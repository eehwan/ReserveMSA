import json
from typing import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from aiokafka import AIOKafkaProducer
from app.services.payment_service import PaymentService

class PaymentEventHandler:
    def __init__(self, kafka_producer: AIOKafkaProducer, db_session_factory: Callable[[], Awaitable[AsyncSession]]):
        self.kafka_producer = kafka_producer
        self.db_session_factory = db_session_factory

    async def handle_payment_requested(self, message):
        """payment_requested 이벤트 처리 - Order Service에서 전송"""
        try:
            event_data = json.loads(message.value.decode('utf-8'))
            print(f"Received payment_requested event: {event_data}")
            
            order_id = event_data.get("order_id")
            amount = event_data.get("amount", 50000)  # 기본값
            
            if not order_id:
                print("Error: order_id not found in payment_requested event")
                return
            
            # DB 세션 생성하여 결제 정보 저장
            async for db_session in self.db_session_factory():
                payment_service = PaymentService(db_session, self.kafka_producer)
                payment_key = await payment_service.handle_payment_requested(order_id, amount)
                print(f"Created payment_key: {payment_key} for order_id: {order_id}")
                
        except Exception as e:
            print(f"Error handling payment_requested event: {e}")