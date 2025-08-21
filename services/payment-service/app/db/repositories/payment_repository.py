from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Payment, PaymentStatus

class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_payment_by_key(self, payment_key: str) -> Payment | None:
        result = await self.db.execute(select(Payment).filter(Payment.payment_key == payment_key))
        return result.scalars().first()

    async def get_payment_by_order_id(self, order_id: str) -> Payment | None:
        result = await self.db.execute(select(Payment).filter(Payment.order_id == order_id))
        return result.scalars().first()

    async def upsert_payment(self, payment_key: str, order_id: str, amount: int, event_id: int = None, seat_num: str = None) -> Payment:
        """
        payment_requested 이벤트 멱등성을 위한 upsert
        동일한 order_id로 여러 번 호출되어도 안전하게 처리
        """
        # PostgreSQL UPSERT 사용 (ON CONFLICT)
        stmt = insert(Payment).values(
            payment_key=payment_key,
            order_id=order_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            event_id=event_id,
            seat_num=seat_num
        )
        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=['order_id'])
        
        await self.db.execute(upsert_stmt)
        await self.db.flush()
        
        return await self.get_payment_by_order_id(order_id)

    async def update_payment_status(self, payment_key: str, status: PaymentStatus, **kwargs) -> Payment | None:
        """
        Webhook 멱등성을 위한 상태 업데이트
        동일한 payment_key + status로 여러 번 호출되어도 안전하게 처리
        """

        # 이미 동일한 상태이면 중복 처리 방지 (멱등성)
        payment = await self.get_payment_by_key(payment_key)
        if not payment:
            return None
        if payment.status == status:
            return payment            
        # 상태 변경이 유효한지 검증
        if not self._is_valid_status_transition(payment.status, status):
            raise ValueError(f"Invalid status transition: {payment.status} -> {status}")
        
        update_data = {"status": status}
        
        # 추가 데이터가 있으면 포함
        if "imp_uid" in kwargs:
            update_data["imp_uid"] = kwargs["imp_uid"]
        if "merchant_uid" in kwargs:
            update_data["merchant_uid"] = kwargs["merchant_uid"]
        if "approved_at" in kwargs:
            update_data["approved_at"] = kwargs["approved_at"]
        if "failure_reason" in kwargs:
            update_data["failure_reason"] = kwargs["failure_reason"]

        query = update(Payment).where(Payment.payment_key == payment_key).values(**update_data)
        await self.db.execute(query)
        await self.db.flush()
        
        return await self.get_payment_by_key(payment_key)
    
    def _is_valid_status_transition(self, current_status: PaymentStatus, new_status: PaymentStatus) -> bool:
        """결제 상태 전이 검증"""
        valid_transitions = {
            PaymentStatus.PENDING: [PaymentStatus.SUCCESS, PaymentStatus.FAILED, PaymentStatus.CANCELLED],
            PaymentStatus.SUCCESS: [],  # 성공 후에는 변경 불가
            PaymentStatus.FAILED: [PaymentStatus.SUCCESS],  # 실패 후 재시도 가능
            PaymentStatus.CANCELLED: []  # 취소 후에는 변경 불가
        }
        
        return new_status in valid_transitions.get(current_status, [])