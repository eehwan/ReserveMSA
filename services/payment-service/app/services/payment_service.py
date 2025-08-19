import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from aiokafka import AIOKafkaProducer
from fastapi import HTTPException

from app.api.v1.schemas.payment_schemas import PaymentWebhookResponse, PaymentStatusResponse
from app.db.repositories import PaymentRepository
from app.db.models import PaymentStatus
from app.core.config import settings

class PaymentService:
    def __init__(self, db: AsyncSession, kafka_producer: AIOKafkaProducer):
        self.db = db
        self.kafka_producer = kafka_producer
        self.payment_repo = PaymentRepository(db)

    async def handle_payment_requested(self, order_id: str, amount: int) -> str:
        """payment_requested 이벤트 처리 - 결제 키 생성 및 DB 저장"""
        try:
            payment_key = f"payment_{uuid.uuid4().hex[:12]}"
            
            # DB에 결제 정보 저장
            await self.payment_repo.create_payment(payment_key, order_id, amount)
            await self.db.commit()
            
            return payment_key
        except Exception as e:
            await self.db.rollback()
            raise e

    async def handle_webhook(self, webhook_data: dict) -> PaymentWebhookResponse:
        """PG사 Webhook 처리"""
        try:
            payment_key = webhook_data["payment_key"]
            order_id = webhook_data["order_id"]
            status = webhook_data["status"]
            
            # 결제 정보 확인
            payment = await self.payment_repo.get_payment_by_key(payment_key)
            if not payment:
                return PaymentWebhookResponse(
                    result="error", 
                    message="Payment not found"
                )
                
            if payment.order_id != order_id:
                return PaymentWebhookResponse(
                    result="error", 
                    message="Order ID mismatch"
                )
            
            # 결제 상태 업데이트
            if status == "SUCCESS":
                await self.payment_repo.update_payment_status(
                    payment_key,
                    PaymentStatus.SUCCESS,
                    imp_uid=webhook_data.get("imp_uid"),
                    merchant_uid=webhook_data.get("merchant_uid"),
                    approved_at=datetime.now()
                )
                
                # payment.verified 이벤트 발행
                await self._publish_payment_event("payment.verified", {
                    "payment_key": payment_key,
                    "order_id": order_id,
                    "amount": webhook_data["amount"],
                    "approved_at": datetime.now().isoformat()
                })
                
            else:  # FAILED
                await self.payment_repo.update_payment_status(
                    payment_key,
                    PaymentStatus.FAILED,
                    imp_uid=webhook_data.get("imp_uid"),
                    merchant_uid=webhook_data.get("merchant_uid"),
                    failure_reason=webhook_data.get("failure_reason", "결제 실패")
                )
                
                # payment.rejected 이벤트 발행
                await self._publish_payment_event("payment.rejected", {
                    "payment_key": payment_key,
                    "order_id": order_id,
                    "amount": webhook_data["amount"],
                    "failure_reason": webhook_data.get("failure_reason", "결제 실패")
                })
            
            await self.db.commit()
            
            return PaymentWebhookResponse(
                result="success",
                message="Webhook processed successfully"
            )
            
        except Exception as e:
            await self.db.rollback()
            return PaymentWebhookResponse(
                result="error",
                message=f"Webhook processing failed: {str(e)}"
            )

    async def get_payment_status(self, payment_key: str) -> PaymentStatusResponse:
        """결제 상태 조회"""
        payment = await self.payment_repo.get_payment_by_key(payment_key)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
        return PaymentStatusResponse(
            payment_key=payment.payment_key,
            order_id=payment.order_id,
            amount=payment.amount,
            status=payment.status.value,
            approved_at=payment.approved_at.isoformat() if payment.approved_at else None,
            failure_reason=payment.failure_reason
        )

    async def _publish_payment_event(self, topic: str, event_data: dict):
        """Kafka 이벤트 발행"""
        try:
            await self.kafka_producer.send_and_wait(
                topic=topic,
                value=event_data
            )
        except Exception as e:
            print(f"Failed to publish payment event to {topic}: {e}")