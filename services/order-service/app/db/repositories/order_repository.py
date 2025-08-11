from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime

from app.db.models import Order, OrderStatus
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
            status=OrderStatus.PENDING,
            lock_key=order_data.lock_key,
            expires_at=order_data.expires_at
        )
        self.db.add(db_order)
        await self.db.commit()
        await self.db.refresh(db_order)
        return db_order

    async def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus,
        payment_key: str = None
    ) -> int:
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        if payment_key:
            update_data["payment_key"] = payment_key

        query = update(Order).where(Order.order_id == order_id)
        result = await self.db.execute(query.values(**update_data))
        await self.db.commit()
        return result.rowcount

    async def cancel_order(self, order_id: str) -> bool:
        result = await self.update_order_status(order_id, OrderStatus.CANCELLED)
        return result > 0

    async def expire_order(self, order_id: str) -> bool:
        result = await self.update_order_status(order_id, OrderStatus.EXPIRED)
        return result > 0

    async def confirm_order(self, order_id: str, payment_key: str) -> bool:
        result = await self.update_order_status(order_id, OrderStatus.CONFIRMED, payment_key)
        return result > 0