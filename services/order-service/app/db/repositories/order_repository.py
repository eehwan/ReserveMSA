from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

from app.db.models import Order
from app.api.v1.schemas import OrderCreate

class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order(self, order_id: int) -> Order | None:
        result = await self.db.execute(select(Order).filter(Order.id == order_id))
        return result.scalars().first()

    async def get_order_by_order_id(self, order_id: str) -> Order | None:
        result = await self.db.execute(select(Order).filter(Order.order_id == order_id))
        return result.scalars().first()

    async def get_orders_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Order]:
        result = await self.db.execute(
            select(Order).filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_order(self, order_data: OrderCreate) -> Order:
        db_order = Order(
            order_id=order_data.order_id,
            user_id=order_data.user_id,
            event_id=order_data.event_id,
            seat_num=order_data.seat_num,
            price=order_data.price,
            lock_key=order_data.lock_key,
            expires_at=order_data.expires_at
        )
        self.db.add(db_order)
        await self.db.flush()
        await self.db.refresh(db_order)
        return db_order

    async def update_payment_key(self, order_id: str, payment_key: str) -> bool:
        """
        결제 완료 시 payment_key 업데이트
        """
        update_data = {
            "payment_key": payment_key,
            "updated_at": datetime.utcnow()
        }
        query = update(Order).where(Order.order_id == order_id)
        result = await self.db.execute(query.values(**update_data))
        await self.db.flush()
        return result.rowcount > 0