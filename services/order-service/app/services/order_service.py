import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from redis.asyncio import Redis
from shared.kafka.producer import KafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.events.publishers import OrderEventPublisher
from app.services.tasks import release_seat_task
from app.api.v1.schemas.order_schemas import OrderResponse
from app.api.v1.schemas import OrderCreate
from app.db.repositories import OrderRepository

class OrderService:
    def __init__(self, redis_client: Redis, kafka_producer: KafkaProducer, db: AsyncSession):
        self.redis_client = redis_client
        self.event_publisher = OrderEventPublisher(kafka_producer)
        self.order_repo = OrderRepository(db)

    async def make_order(self, user_id: int, event_id: int, seat_num: str) -> OrderResponse:
        order_id = f"res_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        redis_key = f"seat:{event_id}:{seat_num}"
        lock_value = f"{user_id}:{order_id}"
        
        is_lock_acquired = await self.redis_client.set(
            redis_key, lock_value, nx=True, ex=settings.SEAT_ORDER_TIMEOUT
        )
        
        if not is_lock_acquired:
            await self.event_publisher.publish_seat_lock_failed(
                user_id=user_id,
                event_id=event_id,
                seat_num=seat_num,
                reason="redis_lock_failed"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seat already reserved.",
            )
            
        try:
            expires_at = datetime.now() + timedelta(seconds=settings.SEAT_ORDER_TIMEOUT)
            
            order_create_data = OrderCreate(
                order_id=order_id,
                user_id=user_id,
                event_id=event_id,
                seat_num=seat_num,
                price=0,  # 실제 가격은 event-service에서 조회해야 함, 임시로 0
                lock_key=lock_value,
                expires_at=expires_at
            )
            await self.order_repo.create_order(order_create_data)
            
            await self.event_publisher.publish_seat_lock(
                order_id=order_id,
                user_id=user_id,
                event_id=event_id,
                seat_num=seat_num,
                lock_key=lock_value,
                expires_at=expires_at
            )

            release_seat_task.apply_async(
                args=[event_id, seat_num, lock_value],
                countdown=settings.SEAT_ORDER_TIMEOUT + 10
            )
            
            await self.order_repo.db.commit()
            
            return OrderResponse(
                order_id=order_id,
                event_id=event_id,
                seat_num=seat_num,
                expires_at=expires_at,
                status="reserved"
            )

        except Exception as e:
            await self.redis_client.delete(redis_key)
            await self.order_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create order: {e}",
            )

    async def cancel_order(self, user_id: int, event_id: int, seat_num: str) -> None:
        redis_key = f"seat:{event_id}:{seat_num}"
        lock_value = await self.redis_client.get(redis_key)

        if not lock_value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or already released.",
            )
        
        # 권한 체크: 본인의 예약인지 확인
        lock_value_str = str(lock_value)
        # id 추출 (lock_value 형식: "user_id:order_id")
        stored_user_id, stored_order_id = lock_value_str.split(":")
        if not str(user_id) == stored_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot cancel other user's order.",
            )

        try:
            cancel_result = await self.order_repo.cancel_order(stored_order_id)
            if not cancel_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found in database.",
                )
            
            await self.redis_client.delete(redis_key)

            await self.event_publisher.publish_seat_unlock(
                event_id=event_id,
                seat_num=seat_num,
                lock_key=lock_value_str
            )
            
            await self.order_repo.db.commit()
            
        except Exception as e:
            await self.order_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel order or publish unlock event: {e}",
            )
