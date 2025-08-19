from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

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

    async def create_payment(self, payment_key: str, order_id: str, amount: int) -> Payment:
        db_payment = Payment(
            payment_key=payment_key,
            order_id=order_id,
            amount=amount,
            status=PaymentStatus.PENDING
        )
        self.db.add(db_payment)
        await self.db.flush()
        await self.db.refresh(db_payment)
        return db_payment

    async def update_payment_status(self, payment_key: str, status: PaymentStatus, **kwargs) -> Payment | None:
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